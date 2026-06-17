from api.database.config.dto_base import BaseDTO, SuccessResponse


class BioPaperResult(BaseDTO):
    """유사도 검색 결과 — 논문 1건."""
    arxiv_id: str
    title: str
    distance: float


class SimilaritySearchResponseWrapper(SuccessResponse):
    """유사도 검색 응답 래퍼: data = 논문 리스트."""
    data: list[BioPaperResult]


class BioSource(BaseDTO):
    """RAG 답변에서 참고한 출처 1건."""
    arxiv_id: str
    title: str


class AskResponse(BaseDTO):
    """RAG 답변 본문."""
    answer: str
    sources: list[BioSource]


class AskResponseWrapper(SuccessResponse):
    """RAG 응답 래퍼: data = AskResponse."""
    data: AskResponse
