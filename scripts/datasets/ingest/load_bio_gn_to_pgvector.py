"""bio_gn_embeddings.jsonl → LangChain PGVector 컬렉션(q-bio-GN) 적재.

기존 embedding 필드는 무시하고 title/abstract로 page_content를 구성한 뒤
LangChain PGVector.aadd_documents로 text-embedding-3-large 임베딩을 새로 생성한다.

주의:
- OpenAI text-embedding-3-large API를 호출하므로 비용이 발생한다 (3,848건, 소액).
- 재실행 시 중복 적재될 수 있다. 컬렉션을 비우려면 pgvector 테이블에서
  collection_name='q-bio-GN'인 행을 직접 삭제한 뒤 재실행한다.
"""

import asyncio
import json
from pathlib import Path

import psycopg
from langchain.embeddings import init_embeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from tqdm import tqdm

JSONL_PATH = Path(__file__).parents[2] / "data" / "raw" / "archive" / "bio_gn_embeddings.jsonl"
COLLECTION_NAME = "bio_embeddings"
CONNECTION = "postgresql+psycopg_async://postgres:postgres@kosa165.iptime.org:50003/postgres"
EMBED_MODEL = "openai:text-embedding-3-large"
BATCH_SIZE = 200


def clear_existing_collection_embeddings() -> None:
    """중복 적재 방지를 위해 기존 bio_embeddings 컬렉션의 임베딩 데이터를 DB에서 삭제합니다."""
    sync_connection_str = CONNECTION.replace("postgresql+psycopg_async://", "postgresql://")
    print(f"      -> DB 연결 및 기존 '{COLLECTION_NAME}' 데이터 제거 시도 중...")
    try:
        with psycopg.connect(sync_connection_str) as conn:
            with conn.cursor() as cur:
                # collection_id 조회
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = %s", (COLLECTION_NAME,))
                row = cur.fetchone()
                if row:
                    collection_uuid = row[0]
                    cur.execute("DELETE FROM langchain_pg_embedding WHERE collection_id = %s", (collection_uuid,))
                    print(f"      -> 기존 '{COLLECTION_NAME}' 컬렉션 임베딩 {cur.rowcount}건 삭제 완료.")
                else:
                    print(f"      -> 기존 '{COLLECTION_NAME}' 컬렉션이 DB에 존재하지 않아 스킵합니다.")
                conn.commit()
    except Exception as e:
        print(f"경고: 기존 데이터 삭제 중 에러 발생 (무시하고 적재 진행): {e}")


def load_documents() -> list[Document]:
    """jsonl 파일을 읽어 Document 리스트로 변환한다."""
    documents = []
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
            except json.JSONDecodeError:
                continue

            title = (paper.get("title") or "").replace("\n", " ").strip()
            abstract = (paper.get("abstract") or "").replace("\n", " ").strip()
            content = f"Title: {title}\n\nAbstract: {abstract}"
            metadata = {
                "arxiv_id": paper.get("arxiv_id", ""),
                "title": title,
                "categories": paper.get("categories", ""),
                "update_date": paper.get("update_date", ""),
            }
            documents.append(Document(page_content=content, metadata=metadata))

    return documents


async def main() -> None:
    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {JSONL_PATH}")

    print(f"[1/3] jsonl 파일 로드 중: {JSONL_PATH}")
    documents = load_documents()
    print(f"      총 {len(documents)}건 로드 완료")

    # 기존 데이터 삭제 (재적재 대응)
    clear_existing_collection_embeddings()

    vectorstore = PGVector(
        embeddings=init_embeddings(model=EMBED_MODEL),
        collection_name=COLLECTION_NAME,
        connection=CONNECTION,
        async_mode=True,
    )

    print(f"[2/3] PGVector 적재 시작 (배치={BATCH_SIZE}, 컬렉션={COLLECTION_NAME})")
    total = 0
    batches = [documents[i:i + BATCH_SIZE] for i in range(0, len(documents), BATCH_SIZE)]
    for batch in tqdm(batches, desc="배치 적재"):
        await vectorstore.aadd_documents(batch)
        total += len(batch)

    print(f"[3/3] 적재 완료: {total}건 → 컬렉션 '{COLLECTION_NAME}'")


if __name__ == "__main__":
    asyncio.run(main())
