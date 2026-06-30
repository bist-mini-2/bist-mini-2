"""ArXiv 대용량 JSONL 덤프 파일에서 생명공학(q-bio) 추가 서브 카테고리를 필터링하여 추가 적재하는 스크립트.

대상 카테고리:
- q-bio.BM (Biomolecules - 6,754건)
- q-bio.MN (Molecular Networks - 4,164건)
- q-bio.TO (Tissues and Organs - 2,619건)
- q-bio.CB (Cell Behavior - 2,454건)
- q-bio.SC (Subcellular Processes - 1,809건)
- q-bio.OT (Other Quantitative Biology - 1,591건)
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Set, List

import psycopg
from dotenv import load_dotenv
from langchain.embeddings import init_embeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from tqdm import tqdm

# 콘솔 출력 한글 인코딩
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 경로 설정
ENV_FILE_PATH = Path(__file__).parents[2] / "backend" / ".env"
SNAPSHOT_PATH = Path(__file__).parents[2] / "data" / "raw" / "archive" / "arxiv-metadata-oai-snapshot.json"
COLLECTION_NAME = "bio_embeddings"

# 설정 로드
load_dotenv(dotenv_path=ENV_FILE_PATH)
CONNECTION = os.getenv("DATABASE_URL")
if not CONNECTION:
    raise ValueError("DATABASE_URL 환경 변수가 설정되어 있지 않습니다. backend/.env 파일을 확인하세요.")

if CONNECTION.startswith("postgresql://"):
    CONNECTION = CONNECTION.replace("postgresql://", "postgresql+psycopg_async://")
elif CONNECTION.startswith("postgresql+asyncpg://"):
    CONNECTION = CONNECTION.replace("postgresql+asyncpg://", "postgresql+psycopg_async://")

EMBED_MODEL = "openai:text-embedding-3-large"

# 기본 대상 서브 카테고리
DEFAULT_TARGET_CATEGORIES = ["q-bio.BM", "q-bio.MN", "q-bio.TO", "q-bio.CB", "q-bio.SC", "q-bio.OT"]

def get_existing_ids(collection_name: str) -> Set[str]:
    """DB에서 지정된 컬렉션에 이미 적재된 arxiv_id 목록을 조회합니다."""
    sync_conn_str = CONNECTION.replace("postgresql+psycopg_async://", "postgresql://")
    existing_ids = set()
    try:
        with psycopg.connect(sync_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (collection_name,))
                row = cur.fetchone()
                if not row:
                    return existing_ids
                collection_uuid = row[0]
                
                cur.execute("""
                    SELECT cmetadata->>'arxiv_id' 
                    FROM langchain_pg_embedding 
                    WHERE collection_id = %s
                """, (collection_uuid,))
                
                rows = cur.fetchall()
                for r in rows:
                    if r[0]:
                        existing_ids.add(r[0])
    except Exception as e:
        print(f"⚠️ 기존 ID 스캔 중 오류 발생 ({collection_name}): {e}")
    return existing_ids

def parse_bio_documents(existing_ids: Set[str], target_categories: List[str], limit: int | None = None) -> List[Document]:
    """ArXiv 대용량 snapshot 파일에서 매칭되는 생명공학 논문을 스트리밍 방식으로 읽어 Document 객체 리스트를 빌드합니다."""
    documents = []
    if not SNAPSHOT_PATH.exists():
        print(f"❌ ArXiv snapshot 파일이 존재하지 않습니다: {SNAPSHOT_PATH}")
        return documents
        
    print(f"🔍 {SNAPSHOT_PATH.name} 스냅샷 파일 스캔 시작...")
    
    count = 0
    # 파일 라인 수 계산 대신 스트리밍 스캔 수행
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if limit is not None and count >= limit:
                break
                
            try:
                paper = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            arxiv_id = paper.get("id") or paper.get("arxiv_id") or ""
            if not arxiv_id or arxiv_id in existing_ids:
                continue
                
            categories_str = paper.get("categories", "")
            cats = categories_str.strip().split()
            
            # 대상 카테고리 중 하나가 포함되어 있는지 확인
            matched = False
            for cat in cats:
                if cat in target_categories:
                    matched = True
                    break
                    
            if not matched:
                continue
                
            title = (paper.get("title") or "").replace("\n", " ").strip()
            abstract = (paper.get("abstract") or "").replace("\n", " ").strip()
            
            # 텍스트 구성 (기존 적재와 형식 통일: Title + Abstract)
            content = f"Title: {title}\n\nAbstract: {abstract}"
            
            metadata = {
                "arxiv_id": arxiv_id,
                "title": title,
                "categories": categories_str,
                "update_date": paper.get("update_date", ""),
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
            count += 1
            if count % 1000 == 0:
                print(f"   -> 임베딩 대기 문서 추출 중... 누적 {count}건")
                
    return documents

async def append_bio_embeddings(documents: List[Document], batch_size: int = 100):
    """생명공학 컬렉션에 비동기 방식으로 신규 문서를 추가 적재합니다."""
    if not documents:
        print("ℹ️ 추가할 신규 생명공학 문서가 없습니다.")
        return
        
    print(f"🚀 생명공학 {len(documents):,}건 추가 적재 시작 (컬렉션: {COLLECTION_NAME}, 배치: {batch_size})...")
    
    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name=COLLECTION_NAME,
        connection=CONNECTION,
        async_mode=True,
    )
    
    total = 0
    batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
    for batch in tqdm(batches, desc="[bio] 배치 적재"):
        await vectorstore.aadd_documents(batch)
        total += len(batch)
        
    print(f"✅ 생명공학 완료: {total:,}건 추가 완료 -> '{COLLECTION_NAME}'")

async def main():
    parser = argparse.ArgumentParser(description="생명공학 추가 데이터 적재 스크립트")
    parser.add_argument("--categories", nargs="+", default=DEFAULT_TARGET_CATEGORIES, help="적재할 q-bio 서브 카테고리 목록")
    parser.add_argument("--limit", type=int, default=None, help="최대 적재 문서 수 (기본값: 제한 없음)")
    parser.add_argument("--batch-size", type=int, default=100, help="한 번에 적재할 배치 크기 (기본값: 100)")
    
    args = parser.parse_args()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 가 설정되어 있지 않습니다.")
        return
        
    print("==================================================")
    print("  생명공학 추가 데이터 적재 프로세스를 시작합니다.")
    print(f"  연결 정보: {CONNECTION}")
    print(f"  모델명: {EMBED_MODEL}")
    print(f"  대상 카테고리: {args.categories}")
    print(f"  최대 제한량: {args.limit}")
    print(f"  배치 크기: {args.batch_size}")
    print("==================================================")

    # 1. 기존 적재된 ID 조회
    print("\n--- [1] 기존 DB 데이터 스캔 ---")
    existing_ids = get_existing_ids(COLLECTION_NAME)
    print(f"   기존 DB에 적재된 생명공학 문서 수: {len(existing_ids):,} 건")
    
    # 2. 신규 문서 파싱
    print("\n--- [2] 원천 snapshot에서 신규 문서 필터링 ---")
    bio_docs = parse_bio_documents(existing_ids, args.categories, args.limit)
    print(f"   적재 후보 신규 생명공학 문서 수: {len(bio_docs):,} 건")
    
    # 3. 추가 적재 진행
    if bio_docs:
        print("\n--- [3] 추가 적재 실행 ---")
        await append_bio_embeddings(bio_docs, args.batch_size)
    else:
        print("   -> 추가 적재할 새로운 문서가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
