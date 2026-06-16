from fastapi import APIRouter

from api.database.config.dto_base import SuccessResponse
from api.v1.cs.models import SimilaritySearchRequest, CsRagQueryRequest
from api.v1.cs.services import CsServiceDep

router = APIRouter(prefix="/similarity-search", tags=["CS RAG Pipeline"])


@router.post(
    "/cs",
    response_model=SuccessResponse,
    summary="컴퓨터 과학 논문 RAG 유사도 검색 API"
)
async def similarity_search_cs(
    request: SimilaritySearchRequest,
    cs_service: CsServiceDep
) -> SuccessResponse:
    """사용자가 보낸 질문(Query)에 대하여 컴퓨터 과학(cs.NE) 논문 데이터베이스에서 
    유사도가 높은 상위 Top-K 청크를 검색하여 반환합니다.

    Args:
        request (SimilaritySearchRequest): 질의어 및 반환 개수 정보 DTO.
        cs_service (CsServiceDep): CS 도메인 비즈니스 로직 처리 서비스 의존성.

    Returns:
        SuccessResponse: 검색 결과 DTO 리스트가 data 영역에 담긴 성공 응답 객체.
    """
    response_data = await cs_service.search_similar_papers(request.query, request.top_k)
    return SuccessResponse(data=response_data)


@router.post(
    "/cs/ask",
    response_model=SuccessResponse,
    summary="컴퓨터 과학 논문 RAG 기반 질의응답 및 답변 생성 API"
)
async def ask_cs_rag(
    request: CsRagQueryRequest,
    cs_service: CsServiceDep
) -> SuccessResponse:
    """사용자가 보낸 질문(Query)에 대하여 cs.NE 논문 DB에서 유사도가 높은 문서를 검색하고,
    검색된 내용을 바탕으로 OpenAI LLM을 사용하여 상세 답변을 생성 및 출처와 함께 반환합니다.

    Args:
        request (CsRagQueryRequest): 질의어, 참고 개수(top_k), 및 사용할 모델명 정보 DTO.
        cs_service (CsServiceDep): CS 도메인 비즈니스 로직 처리 서비스 의존성.

    Returns:
        SuccessResponse: 생성된 답변 및 참고 출처 목록 DTO가 data 영역에 담긴 성공 응답 객체.
    """
    response_data = await cs_service.answer_question_with_rag(
        query=request.query,
        top_k=request.top_k,
        llm_model=request.llm_model
    )
    return SuccessResponse(data=response_data)
