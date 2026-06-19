"""천문학 논문 jsonl → LangChain PGVector 컬렉션(astro-ph-EP) 적재.

astronomy/agent_rag.py 의 search_astronomy_papers 도구가
표준 PGVector(langchain_pg_embedding 테이블)의 'astro-ph-EP' 컬렉션을 검색하므로,
천문학 데이터를 반드시 이 컬렉션 이름으로 적재해야 도구가 찾을 수 있다.

title/abstract로 page_content를 구성한 뒤 text-embedding-3-large로 임베딩을 생성한다.

주의:
- OpenAI text-embedding-3-large API를 호출하므로 비용이 발생한다.
- 재실행 시 중복 적재될 수 있다. 컬렉션을 비우려면 pgvector 테이블에서
  collection_name='astro-ph-EP'인 행을 직접 삭제한 뒤 재실행한다.
- 입력 파일 경로(JSONL_PATH)는 실제 다운로드한 파일 위치로 맞춰야 한다.
"""

import asyncio
import json
from pathlib import Path

from langchain.embeddings import init_embeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector
from tqdm import tqdm

JSONL_PATH = Path(__file__).parents[2] / "data" / "raw" / "archive" / "arxiv-astro-ph-EP-5000.json"
COLLECTION_NAME = "astro-ph-EP"   # 천문학 도구가 찾는 컬렉션 이름과 반드시 일치
CONNECTION = "postgresql+psycopg_async://postgres:postgres@kosa165.iptime.org:50003/postgres"
EMBED_MODEL = "openai:text-embedding-3-large"
BATCH_SIZE = 200


def load_documents() -> list[Document]:
    """jsonl 파일을 읽어 Document 리스트로 변환한다.

    한 줄에 하나의 JSON(jsonl) 형식과, 전체가 하나의 JSON 배열인 형식을 모두 처리한다.
    """
    documents = []
    raw = JSONL_PATH.read_text(encoding="utf-8").strip()

    # 파일이 JSON 배열([...])인지, jsonl(줄마다 객체)인지 자동 판별
    if raw.startswith("["):
        papers = json.loads(raw)
    else:
        papers = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                papers.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    for paper in papers:
        # astro-ph.EP 카테고리만 적재 (혹시 다른 카테고리가 섞여 있을 경우 대비)
        categories = paper.get("categories", "")
        if "astro-ph.EP" not in categories.split():
            continue

        title = (paper.get("title") or "").replace("\n", " ").strip()
        abstract = (paper.get("abstract") or "").replace("\n", " ").strip()
        content = f"Title: {title}\n\nAbstract: {abstract}"
        metadata = {
            "arxiv_id": paper.get("id", ""),       # 원본 arxiv 형식은 'id' 필드
            "title": title,
            "categories": categories,
            "update_date": paper.get("update_date", ""),
        }
        documents.append(Document(page_content=content, metadata=metadata))

    return documents


async def main() -> None:
    if not JSONL_PATH.exists():
        raise FileNotFoundError(
            f"입력 파일을 찾을 수 없습니다: {JSONL_PATH}\n"
            f"  → 스크립트 상단 JSONL_PATH를 실제 다운로드한 파일 경로로 수정하세요."
        )

    print(f"[1/3] 파일 로드 중: {JSONL_PATH}")
    documents = load_documents()
    print(f"      총 {len(documents)}건 로드 완료 (astro-ph.EP)")

    if not documents:
        print("적재할 문서가 없습니다. 파일 내용/카테고리를 확인하세요.")
        return

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