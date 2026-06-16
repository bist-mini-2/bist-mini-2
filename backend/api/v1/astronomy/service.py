import json
import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain.embeddings import init_embeddings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "astro-ph-EP"
CONNECTION = "postgresql+psycopg_async://postgres:postgres@localhost:5432/postgres"
EMBED_MODEL = "openai:text-embedding-3-large"


class AstronomyService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.AstronomyService")

    # --------------------------------------------------------------------------
    # JSON 파일에서 논문 데이터 로드
    # --------------------------------------------------------------------------
    def load_papers(self, file_path: str) -> list[Document]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        documents = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                paper = json.loads(line)
                title = (paper.get("title") or "").replace("\n", " ").strip()
                abstract = (paper.get("abstract") or "").replace("\n", " ").strip()
                content = f"Title: {title}\n\nAbstract: {abstract}"
                metadata = {
                    "arxiv_id": paper.get("id", ""),
                    "title": title,
                    "categories": paper.get("categories", ""),
                    "update_date": paper.get("update_date", ""),
                }
                documents.append(Document(page_content=content, metadata=metadata))

        return documents

    # --------------------------------------------------------------------------
    # PGVector에 임베딩 저장
    # --------------------------------------------------------------------------
    async def save_to_vectorstore(self, documents: list[Document]):
        vectorstore = PGVector(
            embeddings=init_embeddings(model=EMBED_MODEL),
            collection_name=COLLECTION_NAME,
            connection=CONNECTION,
            async_mode=True,
        )
        await vectorstore.aadd_documents(documents)

    # --------------------------------------------------------------------------
    # 유사 논문 검색
    # --------------------------------------------------------------------------
    async def similarity_search(self, query: str, k: int = 3) -> str:
        vectorstore = PGVector(
            embeddings=init_embeddings(model=EMBED_MODEL),
            collection_name=COLLECTION_NAME,
            connection=CONNECTION,
            async_mode=True,
        )
        results = await vectorstore.asimilarity_search_with_score(query, k=k)
        if not results:
            return f"'{query}'와 관련된 논문을 찾을 수 없습니다."

        return "\n".join([
            f"- (유사도: {distance:.4f}): {doc.metadata.get('title', '')[:60]}"
            for doc, distance in results
        ])


# ============================================================
# 의존성 타입 별칭 정의
# ============================================================
AstronomyServiceDep = Annotated[AstronomyService, Depends(AstronomyService)]
