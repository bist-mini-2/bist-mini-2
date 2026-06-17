import json
import logging
import random
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain.embeddings import init_embeddings

from api.common.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "astro-ph-EP"
CONNECTION = settings.PGVECTOR_URL
EMBED_MODEL = "openai:text-embedding-3-large"

# 원본 데이터 경로 (프로젝트 루트 기준)
RAW_DATA_PATH = Path(__file__).parents[4] / "data" / "raw" / "arxiv-metadata-oai-snapshot.json"
SAMPLE_SIZE = 5000
SAMPLE_SEED = 42


class AstronomyService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.AstronomyService")

    # --------------------------------------------------------------------------
    # 원본 파일에서 astro-ph.EP 논문 필터링 + 샘플링 후 Document 변환
    # --------------------------------------------------------------------------
    def load_papers(self) -> list[Document]:
        if not RAW_DATA_PATH.exists():
            raise FileNotFoundError(f"원본 데이터 파일을 찾을 수 없습니다: {RAW_DATA_PATH}")

        ep_papers = []
        with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    paper = json.loads(line)
                    if "astro-ph.EP" in paper.get("categories", "").split():
                        ep_papers.append(paper)
                except json.JSONDecodeError:
                    continue

        self.logger.info(f"astro-ph.EP 전체 논문 수: {len(ep_papers)}")

        random.seed(SAMPLE_SEED)
        sampled = random.sample(ep_papers, min(SAMPLE_SIZE, len(ep_papers)))

        documents = []
        for paper in sampled:
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

        self.logger.info(f"샘플링 완료: {len(documents)}건")
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
