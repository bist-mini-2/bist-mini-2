"""PostgreSQL pgvector DB의 논문 임베딩 데이터를 Hugging Face Dataset 레포지토리에 Parquet 포맷으로 백업/업로드하는 스크립트.

3대 컬렉션(bio_embeddings, cs_embeddings, astronomy_embeddings)을 각각
Hugging Face Dataset의 개별 subset(Config) 혹은 split으로 업로드하여 버전 관리합니다.
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List

import psycopg
from dotenv import load_dotenv
import pandas as pd
from datasets import Dataset, DatasetDict
from tqdm import tqdm

# 콘솔 출력 한글 인코딩 설정
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 경로 설정
ENV_FILE_PATH = Path(__file__).parents[3] / "backend" / ".env"

# 설정 로드
load_dotenv(dotenv_path=ENV_FILE_PATH)
CONNECTION = os.getenv("DATABASE_URL")

# 도메인 컬렉션 맵
DOMAIN_COLLECTIONS = {
    "bio": "bio_embeddings",
    "cs": "cs_embeddings",
    "astronomy": "astronomy_embeddings"
}

def parse_embedding(val) -> List[float]:
    """pgvector의 vector 문자열 또는 리스트 값을 float 리스트로 파싱합니다."""
    if not val:
        return []
    if isinstance(val, list):
        return [float(x) for x in val]
    if isinstance(val, str):
        val = val.strip()
        if val.startswith('[') and val.endswith(']'):
            val = val[1:-1]
        if not val:
            return []
        return [float(x.strip()) for x in val.split(',') if x.strip()]
    # numpy array 등 기타 형식 방어
    try:
        return [float(x) for x in val]
    except Exception:
        return []

def fetch_collection_data(conn_str: str, collection_name: str) -> pd.DataFrame:
    """지정된 컬렉션의 임베딩 및 메타데이터를 PostgreSQL에서 인출하여 Pandas DataFrame으로 빌드합니다."""
    # 동기식 psycopg 커넥션 스트링 변환
    sync_conn_str = conn_str.replace("postgresql+psycopg_async://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"📖 DB에서 컬렉션 스캔 시작: '{collection_name}'...")
    
    data = []
    try:
        with psycopg.connect(sync_conn_str) as conn:
            with conn.cursor() as cur:
                # 1. 컬렉션 UUID 획득
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (collection_name,))
                row = cur.fetchone()
                if not row:
                    print(f"⚠️ 컬렉션 '{collection_name}'이 존재하지 않습니다.")
                    return pd.DataFrame()
                collection_uuid = row[0]
                
                # 2. 임베딩, 본문 및 cmetadata 조회
                cur.execute("""
                    SELECT uuid, embedding, document, cmetadata 
                    FROM langchain_pg_embedding 
                    WHERE collection_id = %s
                """, (collection_uuid,))
                
                rows = cur.fetchall()
                print(f"   -> DB에서 총 {len(rows):,} 건 로드 완료. 파싱을 진행합니다...")
                
                for uuid, embedding, document, cmetadata in tqdm(rows, desc="[파싱 진행]"):
                    meta = cmetadata or {}
                    
                    # cmetadata가 dict 형태가 아닐 경우 json 파싱 방어
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                            
                    arxiv_id = meta.get("arxiv_id") or meta.get("doc_id") or ""
                    title = meta.get("title") or ""
                    categories = meta.get("categories") or ""
                    update_date = meta.get("update_date") or ""
                    
                    parsed_embed = parse_embedding(embedding)
                    
                    data.append({
                        "uuid": str(uuid),
                        "arxiv_id": arxiv_id,
                        "title": title,
                        "categories": categories,
                        "update_date": update_date,
                        "text_chunk": document or "",
                        "embedding": parsed_embed
                    })
                    
    except Exception as e:
        print(f"❌ 데이터 인출 실패 ({collection_name}): {e}")
        sys.exit(1)
        
    return pd.DataFrame(data)

def main():
    parser = argparse.ArgumentParser(description="pgvector DB RAG 임베딩 데이터를 Hugging Face Dataset에 백업/업로드하는 스크립트")
    parser.add_argument("--repo-id", type=str, default="bist-arxiv-domain-embeddings", help="Hugging Face Dataset 레포지토리 ID (기본값: bist-arxiv-domain-embeddings)")
    parser.add_argument("--username", type=str, default=None, help="Hugging Face Username (제공되지 않을 경우 repo-id가 전체 경로여야 합니다)")
    parser.add_argument("--token", type=str, default=None, help="Hugging Face Write Token (없을 경우 HF_TOKEN 환경 변수를 탐색합니다)")
    parser.add_argument("--domains", nargs="+", default=["bio", "cs", "astronomy"], help="적재할 도메인 목록 (기본값: bio cs astronomy)")
    
    args = parser.parse_args()
    
    # HF Token 체크
    hf_token = args.token or os.getenv("HF_TOKEN")
    if not hf_token:
        print("❌ Hugging Face API 토큰이 없습니다. --token 매개변수나 HF_TOKEN 환경 변수를 지정해 주세요.")
        sys.exit(1)
        
    # 데이터베이스 연결 주소 체크
    if not CONNECTION:
        print("❌ DATABASE_URL 이 환경 변수나 backend/.env 파일에 정의되어 있지 않습니다.")
        sys.exit(1)
        
    # 레포지토리 전체 경로 정의
    repo_id = args.repo_id
    if args.username:
        repo_id = f"{args.username}/{repo_id}"
        
    print("==================================================")
    print("  Hugging Face Dataset 업로드 프로세스를 준비합니다.")
    print(f"  대상 레포지토리 ID: {repo_id}")
    print(f"  대상 도메인: {args.domains}")
    print("==================================================")

    # 3대 도메인 데이터셋 사전 빌드
    datasets_dict = {}
    
    for domain in args.domains:
        if domain not in DOMAIN_COLLECTIONS:
            print(f"⚠️ 지원하지 않는 도메인입니다: {domain} -> 스킵")
            continue
            
        collection_name = DOMAIN_COLLECTIONS[domain]
        df = fetch_collection_data(CONNECTION, collection_name)
        
        if df.empty:
            print(f"ℹ️ [{domain}] 추출된 데이터가 없어 스킵합니다.")
            continue
            
        print(f"⚡ Pandas DataFrame을 HF Dataset 객체로 변환합니다. ([{domain}] 건수: {len(df):,}건)...")
        # DataFrame -> Hugging Face Dataset 변환
        dataset = Dataset.from_pandas(df)
        datasets_dict[domain] = dataset
        
    if not datasets_dict:
        print("❌ 업로드할 데이터셋이 비어있어 작업을 중단합니다.")
        sys.exit(1)
        
    # DatasetDict 조립
    dataset_dict = DatasetDict(datasets_dict)
    
    # 4. Hugging Face Hub 업로드 시작
    print(f"\n🚀 Hugging Face Hub 업로드를 시작합니다... (Target: {repo_id})")
    try:
        dataset_dict.push_to_hub(
            repo_id=repo_id,
            token=hf_token,
            private=False  # 공개 범위 설정 (필요시 private=True)
        )
        print(f"🎉 성공적으로 Hugging Face에 데이터셋 업로드 완료! -> https://huggingface.co/datasets/{repo_id}")
    except Exception as e:
        print(f"❌ Hugging Face 업로드 중 치명적인 장애 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
