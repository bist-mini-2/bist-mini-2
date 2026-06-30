from typing import List
from pydantic import Field
from api.database.config.dto_base import BaseDTO


class SimilaritySearchRequest(BaseDTO):
    """유사도 검색 요청을 정의하는 DTO 스키마입니다."""
    query: str = Field(
        ...,
        description="검색할 질의 텍스트",
        examples=["mRNA 백신의 면역 메커니즘"]
    )
    top_k: int = Field(
        3,
        description="반환할 상위 문서 개수",
        ge=1,
        examples=[3]
    )


class SimilaritySearchResultItem(BaseDTO):
    """검색 결과의 개별 논문 정보를 정의하는 DTO 스키마입니다."""
    doc_id: str = Field(..., description="논문 고유 ID")
    title: str = Field(..., description="논문 제목")
    text_chunk: str = Field(..., description="논문 초록 텍스트 청크")
    score: float = Field(..., description="코사인 유사도 (1.0 - distance)")


class SimilaritySearchResponse(BaseDTO):
    """유사도 검색 전체 결과를 정의하는 DTO 스키마입니다."""
    results: List[SimilaritySearchResultItem] = Field(..., description="유사도 검색 결과 목록")
