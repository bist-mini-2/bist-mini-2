from datetime import datetime
from typing import Annotated
from pydantic import Field
from api.database.config.dto_base import BaseDTO, SuccessResponse


class GemCreateRequest(BaseDTO):
    """Gem 생성 요청 스키마."""
    name: Annotated[str, Field(
        min_length=1, 
        max_length=100,
        description="생성할 커스텀 에이전트(Gem)의 이름",
        examples=["유전자 편집 전문 비평가"]
    )]
    db_sources: Annotated[list[str], Field(
        min_length=1,
        description="참고할 학술 도메인 데이터 소스 목록 (bio, cs, astronomy 중 다중 선택)",
        examples=[["bio"]]
    )]
    system_prompt: Annotated[str, Field(
        min_length=1,
        description="에이전트에 바인딩할 페르소나 및 지침 프롬프트",
        examples=["당신은 CRISPR-Cas9 기법 연구 논문만을 집중 분석하여 날카로운 질문을 제안하는 분자생물학 심사위원입니다."]
    )]


class GemResponse(BaseDTO):
    """Gem 단건 응답 스키마."""
    gem_id: str = Field(
        ..., 
        description="커스텀 에이전트(Gem) 고유 식별자 (UUID)", 
        examples=["5c7b827e-8c88-4228-94ef-650a256a2ccd"]
    )
    name: str = Field(
        ..., 
        description="커스텀 에이전트(Gem) 이름", 
        examples=["유전자 편집 전문 비평가"]
    )
    db_sources: list[str] = Field(
        ..., 
        description="참고 중인 학술 데이터 소스 목록", 
        examples=[["bio"]]
    )
    system_prompt: str = Field(
        ..., 
        description="설정된 지침 프롬프트", 
        examples=["당신은 CRISPR-Cas9 기법 연구 논문만을 집중 분석하여 날카로운 질문을 제안하는 분자생물학 심사위원입니다."]
    )
    created_at: datetime = Field(
        ..., 
        description="생성 일시", 
        examples=["2026-06-23T11:22:00"]
    )


class GemListResponseWrapper(SuccessResponse):
    """Gem 목록 응답 래퍼."""
    data: list[GemResponse] = Field(
        ..., 
        description="사용자가 생성하여 소유 중인 Gem 에이전트 목록"
    )


class GemResponseWrapper(SuccessResponse):
    """Gem 단건 응답 래퍼."""
    data: GemResponse = Field(
        ..., 
        description="생성/조회된 커스텀 Gem 에이전트 상세 정보"
    )


class GemUpdateRequest(BaseDTO):
    """Gem 수정 요청 스키마. 전달된 필드만 업데이트한다."""
    name: Annotated[str, Field(
        min_length=1, 
        max_length=100,
        description="수정할 커스텀 에이전트 이름 (선택)",
        examples=["수정된 유전자 편집 비평가"]
    )] | None = None
    db_sources: Annotated[list[str], Field(
        min_length=1,
        description="수정할 데이터 소스 목록 (선택)",
        examples=[["bio", "cs"]]
    )] | None = None
    system_prompt: Annotated[str, Field(
        min_length=1,
        description="수정할 지침 프롬프트 (선택)",
        examples=["새롭게 업데이트된 분자생물학 비평 지침 프롬프트"]
    )] | None = None


class GemChatRequest(BaseDTO):
    """Gem 대화 요청 스키마."""
    thread_id: str = Field(
        ..., 
        description="대화 세션 고유 스레드 ID (UUID/식별자)", 
        examples=["thread_9c7b827e-8c88-4228"]
    )
    message: str = Field(
        ..., 
        description="에이전트에게 전송할 대화 내용", 
        examples=["CRISPR 기법의 전달 시스템(Delivery System) 최근 한계점은 무엇인가?"]
    )


class GemChatResponse(BaseDTO):
    """Gem 대화 응답 스키마."""
    answer: str = Field(
        ..., 
        description="Gem 에이전트가 생성한 마크다운 형식 답변 텍스트", 
        examples=["CRISPR 기법의 가장 큰 전달 한계는 아데노 연관 바이러스(AAV)의 크기 제한 및 비특이적 면역 반응입니다..."]
    )
    papers: list[dict] = Field(
        default_factory=list, 
        description="LLM이 답변 내에서 인용하여 요약 정리한 논문 목록", 
        examples=[[{
            "arxiv_id": "2402.12345", 
            "title": "AAV-mediated CRISPR Delivery Constraints", 
            "summary": "This paper addresses packaging capacity limits of AAV vectors for Cas9 constructs."
        }]]
    )
    sources: list[dict] = Field(
        default_factory=list, 
        description="RAG 검색 엔진이 찾아낸 가공되지 않은 실제 논문 청크 정보 목록", 
        examples=[[{
            "arxiv_id": "2402.12345", 
            "title": "AAV-mediated CRISPR Delivery Constraints", 
            "text_chunk": "AAV vectors have a cargo limit of approximately 4.7 kb, which restricts large Cas9 variants...", 
            "score": 0.8123
        }]]
    )


class GemChatResponseWrapper(SuccessResponse):
    """Gem 대화 응답 래퍼."""
    data: GemChatResponse = Field(
        ..., 
        description="Gem RAG 대화 응답 및 검색 출처 결과 본문"
    )
