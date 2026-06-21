import logging
from typing import Annotated

from fastapi import APIRouter, Form
from fastapi.responses import PlainTextResponse

from api.v1.astronomy.service import AstronomyServiceDep
from api.v1.astronomy.agent_rag import AstronomyRAGAgentDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/astronomy", tags=["astronomy"])


@router.post("/embedding", response_class=PlainTextResponse)
async def embedding(service: AstronomyServiceDep):
    """원본 데이터에서 astro-ph.EP 논문 5000건을 필터링하여 PGVector에 임베딩합니다."""
    documents = service.load_papers()
    await service.save_to_vectorstore(documents)
    return f"✅ 임베딩 완료!\n- 총 논문 수: {len(documents)}건\n- 컬렉션: astro-ph-EP"


@router.post("/similarity-search", response_class=PlainTextResponse)
async def similarity_search(
    query: Annotated[str, Form()],
    service: AstronomyServiceDep,
    k: Annotated[int, Form()] = 3,
):
    """질문과 유사한 논문을 검색합니다."""
    result = await service.similarity_search(query=query, k=k)
    return result


@router.post("/ask", response_class=PlainTextResponse)
async def ask(
    question: Annotated[str, Form()],
    agent: AstronomyRAGAgentDep,
):
    """지구·행성 천체물리학 관련 질문에 RAG 기반으로 답변합니다."""
    response = await agent.run(question)
    return response
