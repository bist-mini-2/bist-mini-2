from fastapi import APIRouter

from api.database.config.dto_base import SuccessResponse
from api.v1.cs.models import SimilaritySearchRequest
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
