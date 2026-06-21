import logging
from typing import Annotated

from fastapi import APIRouter, Form

from api.v1.bio.agent_rag import BioRagAgentDep
from api.v1.bio.models import (
    AskResponse,
    AskResponseWrapper,
    BioSource,
    SimilaritySearchResponseWrapper,
)
from api.v1.bio.service import BioEmbeddingServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bio", tags=["bio"])


# 테스트용
@router.post("/similarity-search")
async def similarity_search(
    query: Annotated[str, Form()],
    service: BioEmbeddingServiceDep,
    k: Annotated[int, Form()] = 3,
) -> SimilaritySearchResponseWrapper:
    """질문과 유사한 q-bio.GN 논문을 검색합니다 (검색 테스트용)."""
    results = await service.similarity_search(query=query, k=k)
    return SimilaritySearchResponseWrapper(data=results)


@router.post("/ask")
async def ask(
    question: Annotated[str, Form()],
    agent: BioRagAgentDep,
) -> AskResponseWrapper:
    """생명공학·유전체학 관련 질문에 RAG 기반으로 답변합니다."""
    result = await agent.run(question)   # {"answer": ..., "sources": [...]}

    return AskResponseWrapper(
        data=AskResponse(
            answer=result["answer"],
            sources=[BioSource(**s) for s in result["sources"]],
        )
    )
