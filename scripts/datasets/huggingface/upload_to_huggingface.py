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
    """지정된 컬렉션의 임베딩 및 메타데이터를 5,000건씩 분할 인출(Paging)하여 Pandas DataFrame으로 빌드합니다."""
    # 동기식 psycopg 커넥션 스트링 변환
    sync_conn_str = conn_str.replace("postgresql+psycopg_async://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"📖 DB에서 컬렉션 스캔 시작: '{collection_name}'...")
    
    data = []
    chunk_size = 5000  # 원격 네트워크 전송 안정성을 위해 5,000건씩 분할 스캔
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
                
                # 2. 총 레코드 카운트 획득
                cur.execute("SELECT count(*) FROM langchain_pg_embedding WHERE collection_id = %s", (collection_uuid,))
                total_records = cur.fetchone()[0]
                print(f"   -> 총 {total_records:,} 건의 레코드가 감지되었습니다. 분할 다운로드를 시작합니다...")
                
                offset = 0
                pbar = tqdm(total=total_records, desc=f"[{collection_name} 다운로드]")
                while offset < total_records:
                    cur.execute("""
                        SELECT id, embedding, document, cmetadata 
                        FROM langchain_pg_embedding 
                        WHERE collection_id = %s
                        ORDER BY id
                        LIMIT %s OFFSET %s
                    """, (collection_uuid, chunk_size, offset))
                    
                    rows = cur.fetchall()
                    if not rows:
                        break
                        
                    for row_id, embedding, document, cmetadata in rows:
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
                            "uuid": str(row_id),
                            "arxiv_id": arxiv_id,
                            "title": title,
                            "categories": categories,
                            "update_date": update_date,
                            "text_chunk": document or "",
                            "embedding": parsed_embed
                        })
                    
                    offset += len(rows)
                    pbar.update(len(rows))
                pbar.close()
                
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
    
    parser.add_argument("--private", action="store_true", help="Hugging Face Dataset 레포지토리를 private으로 비공개 설정합니다.")
    
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
    print(f"  공개 범위: {'Private' if args.private else 'Public'}")
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
            private=args.private
        )
        print(f"🎉 성공적으로 Hugging Face에 데이터셋 업로드 완료! -> https://huggingface.co/datasets/{repo_id}")
        
        # 5. README.md (Dataset Card) 자동 업로드 진행
        print("📝 Hugging Face Dataset Card (README.md) 생성 및 업로드를 시작합니다...")
        from huggingface_hub import HfApi
        
        readme_content = f"""---
license: mit
task_categories:
- text-retrieval
language:
- en
tags:
- rag
- academic
- arxiv
- embedding
---

# BIST ArXiv Domain Embeddings Dataset (Private)

본 데이터셋은 **'논문 AI 에이전트 채팅 플랫폼 (Bist Mini 2)'**의 RAG 및 검색 엔진의 소스로 활용하기 위해 구축된 3대 학술 도메인 특화 벡터 임베딩 데이터셋입니다.

## 🔍 1. 데이터 기원 및 출처 (Data Source)
* **원본 데이터셋:** Kaggle [ArXiv Dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv) (`arxiv-metadata-oai-snapshot.json`)
* **데이터 정제 규칙:** Kaggle ArXiv 덤프 파일 내에서 아래 서브 카테고리를 대상으로 필터링을 수행하여 로컬 pgvector 데이터베이스에 1차 가공 적재했습니다.
  - **Quantitative Biology (bio):** `q-bio.QM`, `q-bio.PE`, `q-bio.NC`, `q-bio.BM`, `q-bio.MN`, `q-bio.GN`, `q-bio.TO`, `q-bio.CB`, `q-bio.SC`, `q-bio.OT` (총 54,066 건)
  - **Computer Science (cs):** `cs.NE` 등 (총 17,825 건)
  - **Astronomy (astronomy):** `astro-ph.EP` 등 (총 35,083 건)

## ⚡ 2. 임베딩 변환 및 인코딩 스펙 (Embedding Specification)
* **임베딩 모델:** OpenAI **`text-embedding-3-large`** (3072차원)
* **인코딩 구조:** 각 논문의 제목(`title`)과 초록(`abstract`)을 결합하여 아래와 같은 형식의 텍스트 본문을 빌드하고 이를 3072차원 벡터로 변환했습니다.
  ```text
  Title: {{논문 제목}}

  Abstract: {{논문 초록 본문}}
  ```

## 📂 3. 데이터셋 스키마 (Dataset Schema)
본 데이터셋은 `bio`, `cs`, `astronomy` 3개의 Subset(Config)으로 분리하여 관리되며, 각 레코드는 다음 필드를 지닙니다.
* `uuid`: pgvector DB의 기본 키 (langchain_pg_embedding.id)
* `arxiv_id`: ArXiv 논문 고유 식별자 (예: `1910.12345`)
* `title`: 논문 제목
* `categories`: 공백 구분된 ArXiv 카테고리 태그
* `update_date`: 논문 업데이트 날짜
* `text_chunk`: 임베딩의 근거가 된 원문 텍스트 (Title + Abstract)
* `embedding`: 3072차원 float 벡터 어레이 데이터
"""
        api = HfApi()
        api.upload_file(
            path_or_fileobj=readme_content.encode("utf-8"),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            token=hf_token
        )
        print("✅ Dataset Card (README.md) 업로드 성공!")
        
    except Exception as e:
        print(f"❌ Hugging Face 업로드 중 치명적인 장애 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
