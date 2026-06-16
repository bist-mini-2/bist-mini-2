from typing import List
from pydantic import Field
from api.database.config.dto_base import BaseDTO


class SimilaritySearchRequest(BaseDTO):
    """컴퓨터 과학 논문 유사도 검색 요청 DTO 클래스입니다.

    Attributes:
        query (str): 검색할 질의어 본문.
        top_k (int): 반환할 유사 텍스트 청크 상위 개수 (기본값: 3).
    """
    
    query: str = Field(
        ...,
        description="검색할 질문이나 텍스트 키워드",
        examples=["Explain neural network training dynamics."]
    )
    top_k: int = Field(
        3,
        description="가장 유사도가 높은 상위 결과 개수",
        ge=1,
        le=10
    )


class SimilaritySearchResult(BaseDTO):
    """유사도 검색 성공 시 반환되는 개별 청크 결과 구조체 DTO 클래스입니다.

    Attributes:
        doc_id (str): 논문 고유 ID.
        title (str): 논문 제목.
        text_chunk (str): 유사성이 매칭된 실제 500자 텍스트 청크.
        score (float): 코사인 유사도 점수 (0 ~ 1).
    """
    
    doc_id: str = Field(..., description="ArXiv 논문 고유 ID")
    title: str = Field(..., description="논문 제목")
    text_chunk: str = Field(..., description="매칭된 텍스트 청크 본문")
    score: float = Field(..., description="코사인 유사도 점수 (1에 가까울수록 유사함)")


class SimilaritySearchResponse(BaseDTO):
    """유사도 검색 성공 시 최종적으로 data 영역에 바인딩되어 반환되는 DTO 클래스입니다.

    Attributes:
        results (List[SimilaritySearchResult]): 유사 검색 결과 목록.
    """
    
    results: List[SimilaritySearchResult] = Field(
        ...,
        description="검색 결과 유사도 순위 리스트"
    )


class CsRagQueryRequest(BaseDTO):
    """컴퓨터 과학 논문 RAG 질의 및 텍스트 생성 요청 DTO 클래스입니다.

    Attributes:
        query (str): 질문할 본문 텍스트.
        top_k (int): 참고할 상위 텍스트 청크 개수 (기본값: 3).
        llm_model (str): 생성에 활용할 LLM 모델명 (기본값: "gpt-4o-mini").
    """

    query: str = Field(
        ...,
        description="질문할 질문 내용",
        examples=["How does evolutionary computing work?"]
    )
    top_k: int = Field(
        3,
        description="참고할 유사 논문 청크 상위 개수",
        ge=1,
        le=10
    )
    llm_model: str = Field(
        "gpt-4o-mini",
        description="사용할 LLM 모델명 (예: gpt-4o-mini, gpt-4o)"
    )


class CsRagQueryResponse(BaseDTO):
    """컴퓨터 과학 논문 RAG 답변 및 출처 정보 응답 DTO 클래스입니다.

    Attributes:
        answer (str): 생성된 최종 답변 텍스트.
        sources (List[SimilaritySearchResult]): 답변 작성에 참고한 유사 논문 청크 목록.
    """

    answer: str = Field(..., description="생성된 답변 텍스트")
    sources: List[SimilaritySearchResult] = Field(..., description="참고한 논문 출처 리스트")


class CsAgentQueryRequest(BaseDTO):
    """컴퓨터 과학 논문 RAG 툴 바인딩 에이전트 요청 DTO 클래스입니다.

    Attributes:
        query (str): 에이전트에게 전달할 질문 본문.
        llm_model (str): 생성에 활용할 LLM 모델명 (기본값: "gpt-4o-mini").
    """

    query: str = Field(
        ...,
        description="에이전트에게 질문할 질문 내용",
        examples=["Explain neural network training dynamics and what papers discuss it."]
    )
    llm_model: str = Field(
        "gpt-4o-mini",
        description="사용할 LLM 모델명 (예: gpt-4o-mini, gpt-4o)"
    )


class CsAgentQueryResponse(BaseDTO):
    """컴퓨터 과학 논문 RAG 툴 바인딩 에이전트 응답 DTO 클래스입니다.

    Attributes:
        answer (str): 에이전트가 생성한 최종 답변 텍스트.
        tool_calls (List[dict]): 에이전트가 답변을 생성하기 위해 호출한 툴 정보 리스트.
    """

    answer: str = Field(..., description="에이전트가 생성한 답변 텍스트")
    tool_calls: List[dict] = Field(default=[], description="실행된 툴 호출 내역 정보 리스트")
