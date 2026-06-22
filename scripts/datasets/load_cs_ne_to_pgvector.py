"""cs.NE 논문 jsonl → LangChain PGVector 컬렉션(cs-NE) 적재.

data/raw/archive/local_embeddings_no_chunk_output.jsonl 에 이미 3072차원 임베딩이 존재하므로,
이를 파싱하여 OpenAI API 호출 비용 없이 빠르게 표준 PGVector 테이블로 일괄 적재합니다.
이 과정에서 q-bio.GN, astro-ph-EP 컬렉션과 동일하게 메타데이터 포맷을 다음 4개 키로 강제 구성합니다:
{
  "title": ...,
  "arxiv_id": ...,
  "categories": ...,
  "update_date": ...
}
update_date는 data/raw/archive/arxiv-metadata-oai-snapshot.json 파일에서 동적으로 매핑합니다.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict

import psycopg
from langchain.embeddings import init_embeddings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVector
from tqdm import tqdm

# 콘솔 출력 한글 인코딩 설정
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

JSONL_PATH = Path(__file__).parents[2] / "data" / "raw" / "archive" / "local_embeddings_no_chunk_output.jsonl"
SNAPSHOT_PATH = Path(__file__).parents[2] / "data" / "raw" / "archive" / "arxiv-metadata-oai-snapshot.json"
COLLECTION_NAME = "cs_embeddings"
CONNECTION = "postgresql+psycopg_async://postgres:postgres@kosa165.iptime.org:50003/postgres"
EMBED_MODEL = "openai:text-embedding-3-large"
BATCH_SIZE = 200


class OrderedPrecomputedEmbeddings(Embeddings):
    """배치 적재 시 전달되는 문서들의 임베딩을 캐싱된 임베딩 리스트에서 순서대로 꺼내어 반환하는 커스텀 Embeddings 어댑터."""

    def __init__(self, embeddings: List[List[float]]):
        self.embeddings = embeddings
        self._index = 0

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        start = self._index
        end = start + len(texts)
        self._index = end
        if start >= len(self.embeddings):
            return [[0.0] * 3072 for _ in texts]
        return self.embeddings[start:end]

    def embed_query(self, text: str) -> List[float]:
        return [0.0] * 3072


def load_update_date_map() -> Dict[str, str]:
    """arxiv-metadata-oai-snapshot.json 파일을 읽어 cs.NE 논문의 update_date 매핑을 빌드합니다."""
    mapping = {}
    if not SNAPSHOT_PATH.exists():
        print(f"경고: {SNAPSHOT_PATH} 파일이 없어 update_date를 공란으로 채웁니다.")
        return mapping

    print(f"      -> {SNAPSHOT_PATH.name} 스캔 중...")
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if "cs.NE" not in line:
                continue
            try:
                data = json.loads(line)
                categories = data.get("categories", "")
                if "cs.NE" in categories.split():
                    mapping[data["id"]] = data.get("update_date", "")
            except (json.JSONDecodeError, KeyError):
                continue
    return mapping


def load_documents_with_cached_embeddings(update_date_map: Dict[str, str]) -> tuple[list[Document], list[list[float]], bool]:
    """jsonl 파일을 읽어 Document 리스트와 해당 precomputed 임베딩 벡터 목록을 반환합니다."""
    documents = []
    cached_embeddings = []
    has_all_embeddings = True

    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                paper = json.loads(line)
            except json.JSONDecodeError:
                continue

            doc_id = paper.get("doc_id") or paper.get("id") or ""
            title = (paper.get("title") or "").replace("\n", " ").strip()
            abstract = (paper.get("abstract") or "").replace("\n", " ").strip()
            categories = paper.get("categories", "")
            update_date = update_date_map.get(doc_id, "")
            
            content = abstract
            
            # 메타데이터를 요청받은 4개 키 형식으로 정확하게 구성
            metadata = {
                "title": title,
                "arxiv_id": doc_id,
                "categories": categories,
                "update_date": update_date,
            }
            
            chunks = paper.get("chunks", [])
            embedding = None
            if chunks and isinstance(chunks, list):
                embedding = chunks[0].get("embedding")

            if embedding and len(embedding) == 3072:
                cached_embeddings.append(embedding)
            else:
                has_all_embeddings = False
                
            documents.append(Document(page_content=content, metadata=metadata))

    return documents, cached_embeddings, has_all_embeddings


def clear_existing_collection_embeddings() -> None:
    """중복 적재 방지를 위해 기존 cs-NE 컬렉션의 임베딩 데이터를 DB에서 삭제합니다."""
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


async def main() -> None:
    if not JSONL_PATH.exists():
        raise FileNotFoundError(f"입력 데이터 캐시 파일을 찾을 수 없습니다: {JSONL_PATH}")

    print("[1/4] update_date 메타데이터 매핑 정보 빌드 중...")
    update_date_map = load_update_date_map()
    print(f"      총 {len(update_date_map)}건의 cs.NE 날짜 정보 수집 완료")

    print(f"[2/4] jsonl 데이터 로드 및 4-키 메타데이터 구성 중: {JSONL_PATH}")
    documents, cached_embeddings, has_all_embeddings = load_documents_with_cached_embeddings(update_date_map)
    print(f"      총 {len(documents)}건 문서 구성 완료")

    # 기존 데이터 삭제 (재적재 대응)
    clear_existing_collection_embeddings()

    if has_all_embeddings and len(cached_embeddings) == len(documents):
        print(f"      -> {len(cached_embeddings)}건의 precomputed 임베딩 데이터가 확인되었습니다. (OpenAI API 호출 생략)")
        embeddings_impl = OrderedPrecomputedEmbeddings(cached_embeddings)
    else:
        print("      -> 캐싱된 임베딩이 불완전합니다. OpenAI API(text-embedding-3-large)를 통해 임베딩을 생성합니다.")
        if not os.getenv("OPENAI_API_KEY"):
            print("오류: OpenAI API 호출이 필요하지만 OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            return
        embeddings_impl = init_embeddings(model=EMBED_MODEL)

    vectorstore = PGVector(
        embeddings=embeddings_impl,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION,
        async_mode=True,
    )

    print(f"[3/4] 표준 PGVector 적재 시작 (배치={BATCH_SIZE}, 컬렉션={COLLECTION_NAME})")
    total = 0
    batches = [documents[i:i + BATCH_SIZE] for i in range(0, len(documents), BATCH_SIZE)]
    for batch in tqdm(batches, desc="배치 적재"):
        await vectorstore.aadd_documents(batch)
        total += len(batch)

    print(f"[4/4] 적재 완료: {total}건 → 컬렉션 '{COLLECTION_NAME}'")


if __name__ == "__main__":
    asyncio.run(main())
