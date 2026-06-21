import logging
from typing import Annotated

from fastapi import Depends
from langchain.embeddings import init_embeddings
from langchain_postgres import PGVector

from api.v1.bio.models import BioPaperResult
from api.v1.bio.vectorstore_conf import COLLECTION_NAME, CONNECTION, EMBED_MODEL

logger = logging.getLogger(__name__)


class BioEmbeddingService:
    """q-bio.GN 논문 유사도 검색 서비스."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.BioEmbeddingService")

    async def similarity_search(self, query: str, k: int = 3) -> list[BioPaperResult]:
        """쿼리와 유사한 q-bio.GN 논문을 검색하여 BioPaperResult 리스트로 반환한다."""
        vectorstore = PGVector(
            embeddings=init_embeddings(model=EMBED_MODEL),
            collection_name=COLLECTION_NAME,
            connection=CONNECTION,
            async_mode=True,
        )
        results = await vectorstore.asimilarity_search_with_score(query, k=k)
        if not results:
            return []

        return [
            BioPaperResult(
                arxiv_id=doc.metadata.get("arxiv_id", ""),
                title=doc.metadata.get("title", ""),
                distance=distance,
            )
            for doc, distance in results
        ]


# ============================================================
# 의존성 타입 별칭 정의
# ============================================================
BioEmbeddingServiceDep = Annotated[BioEmbeddingService, Depends(BioEmbeddingService)]
