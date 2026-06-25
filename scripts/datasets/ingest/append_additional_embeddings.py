"""기존 pgvector DB에 적재되지 않은 새로운 CS 및 천문학 논문을 추가 적재하는 스크립트."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Set

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
CS_RAW_PATH = Path(__file__).parents[2] / "data" / "raw" / "archive" / "cs_raw.json"
ASTRO_RAW_PATH = Path(__file__).parents[2] / "data" / "raw" / "archive" / "astronomy_raw.json"

# 설정 로드
load_dotenv(dotenv_path=ENV_FILE_PATH)
CONNECTION = os.getenv("DATABASE_URL")
if not CONNECTION:
    raise ValueError("DATABASE_URL 환경 변수가 설정되어 있지 않습니다.")

# langchain_postgres 용 비동기 드라이버 이름 치환
if CONNECTION.startswith("postgresql://"):
    CONNECTION = CONNECTION.replace("postgresql://", "postgresql+psycopg_async://")
elif CONNECTION.startswith("postgresql+asyncpg://"):
    CONNECTION = CONNECTION.replace("postgresql+asyncpg://", "postgresql+psycopg_async://")

EMBED_MODEL = "openai:text-embedding-3-large"
BATCH_SIZE = 100
LIMIT_COUNT = 5000

# 도메인 컬렉션 맵
DOMAIN_COLLECTIONS = {
    "cs": "cs_embeddings",
    "astronomy": "astronomy_embeddings"
}

def get_existing_ids(collection_name: str) -> Set[str]:
    """DB에서 지정된 컬렉션에 이미 적재된 arxiv_id 목록을 조회합니다."""
    # 동기식 커넥션 스트링 변환
    sync_conn_str = CONNECTION.replace("postgresql+psycopg_async://", "postgresql://")
    existing_ids = set()
    try:
        with psycopg.connect(sync_conn_str) as conn:
            with conn.cursor() as cur:
                # 1. 컬렉션 UUID 획득
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (collection_name,))
                row = cur.fetchone()
                if not row:
                    return existing_ids
                collection_uuid = row[0]
                
                # 2. 메타데이터에서 arxiv_id 목록 스캔
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

def load_new_documents(file_path: Path, existing_ids: Set[str], limit: int) -> list[Document]:
    """JSON raw 파일에서 기존에 존재하지 않는 신규 문서를 선별하여 Document 객체 목록을 빌드합니다."""
    documents = []
    if not file_path.exists():
        print(f"❌ 원본 파일이 존재하지 않습니다: {file_path}")
        return documents
        
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            papers = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 에러 ({file_path.name}): {e}")
            return documents
            
    count = 0
    for paper in papers:
        if count >= limit:
            break
            
        arxiv_id = paper.get("id") or paper.get("arxiv_id") or ""
        if not arxiv_id or arxiv_id in existing_ids:
            continue
            
        title = (paper.get("title") or "").replace("\n", " ").strip()
        abstract = (paper.get("abstract") or "").replace("\n", " ").strip()
        
        # 텍스트 구성 (기존 적재와 형식 통일)
        content = f"Title: {title}\n\nAbstract: {abstract}"
        
        # 메타데이터 4개 필드 강제
        metadata = {
            "arxiv_id": arxiv_id,
            "title": title,
            "categories": paper.get("categories", ""),
            "update_date": paper.get("update_date", ""),
        }
        
        documents.append(Document(page_content=content, metadata=metadata))
        count += 1
        
    return documents

async def append_domain_embeddings(domain: str, documents: list[Document]):
    """지정된 도메인 컬렉션에 비동기 방식으로 신규 문서를 추가 적재합니다."""
    if not documents:
        print(f"ℹ️ [{domain}] 추가할 신규 문서가 없습니다.")
        return
        
    collection_name = DOMAIN_COLLECTIONS[domain]
    print(f"🚀 [{domain}] {len(documents)}건 추가 적재 시작 (컬렉션: {collection_name})...")
    
    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name=collection_name,
        connection=CONNECTION,
        async_mode=True,
    )
    
    total = 0
    batches = [documents[i:i + BATCH_SIZE] for i in range(0, len(documents), BATCH_SIZE)]
    for batch in tqdm(batches, desc=f"[{domain}] 배치 적재"):
        await vectorstore.aadd_documents(batch)
        total += len(batch)
        
    print(f"✅ [{domain}] 완료: {total}건 추가 완료 -> '{collection_name}'")

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 가 설정되어 있지 않습니다.")
        return
        
    # 1. CS 추가 적재 진행
    print("\n--- [1/2] 컴퓨터 과학 (CS) 추가 적재 ---")
    cs_existing = get_existing_ids(DOMAIN_COLLECTIONS["cs"])
    print(f"   기존 DB에 적재된 CS 문서 수: {len(cs_existing):,} 건")
    cs_docs = load_new_documents(CS_RAW_PATH, cs_existing, LIMIT_COUNT)
    print(f"   적재 후보 신규 CS 문서 수: {len(cs_docs):,} 건")
    await append_domain_embeddings("cs", cs_docs)
    
    # 2. Astronomy 추가 적재 진행
    print("\n--- [2/2] 천문학 (Astronomy) 추가 적재 ---")
    astro_existing = get_existing_ids(DOMAIN_COLLECTIONS["astronomy"])
    print(f"   기존 DB에 적재된 천문학 문서 수: {len(astro_existing):,} 건")
    astro_docs = load_new_documents(ASTRO_RAW_PATH, astro_existing, LIMIT_COUNT)
    print(f"   적재 후보 신규 천문학 문서 수: {len(astro_docs):,} 건")
    await append_domain_embeddings("astronomy", astro_docs)

if __name__ == "__main__":
    asyncio.run(main())
