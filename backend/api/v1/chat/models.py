from datetime import datetime
from typing import Annotated
from pydantic import Field
from api.database.config.dto_base import BaseDTO, SuccessResponse


class ChatSessionCreateRequest(BaseDTO):
    """채팅방 생성 요청 스키마. 방 제목을 입력받는다."""
    title: Annotated[str, Field(
        min_length=1, 
        max_length=100, 
        description="생성할 대화 세션의 제목", 
        examples=["새로운 생명공학 RAG 대화방"]
    )]


class ChatSessionUpdateRequest(BaseDTO):
    """채팅방 제목 수정 요청 DTO."""
    title: Annotated[str, Field(
        min_length=1, 
        max_length=100, 
        description="변경할 대화 세션의 새 제목", 
        examples=["수정된 컴퓨터과학 RAG 대화방"]
    )]


class ChatSessionResponse(BaseDTO):
    """채팅방(세션) 단건 응답 스키마."""
    session_id: str = Field(
        ..., 
        description="대화 세션 고유 식별자 (UUID)", 
        examples=["9c7b827e-8c88-4228-94ef-650a256a2ccd"]
    )
    title: str = Field(
        ..., 
        description="대화 세션 제목", 
        examples=["새로운 생명공학 RAG 대화방"]
    )
    created_at: datetime = Field(
        ..., 
        description="세션 생성 일시", 
        examples=["2026-06-23T11:22:00"]
    )


class ChatSessionListResponseWrapper(SuccessResponse):
    """채팅방 목록 응답 래퍼: data = 채팅방 리스트."""
    data: list[ChatSessionResponse] = Field(
        ..., 
        description="조회된 대화 세션 목록"
    )


class ChatSessionResponseWrapper(SuccessResponse):
    """채팅방 단건 응답 래퍼: data = 채팅방."""
    data: ChatSessionResponse = Field(
        ..., 
        description="생성/수정된 대화 세션 정보"
    )


class ChatMessageRequest(BaseDTO):
    """채팅방 메시지 전송 요청 스키마."""
    message: str = Field(
        ..., 
        description="에이전트에게 보낼 대화 메시지 텍스트", 
        examples=["CRISPR-Cas9 유전자 편집 기법의 최신 동향을 알려줘."]
    )


class ChatMessageResponse(BaseDTO):
    """RAG 답변 본문. bio RAG와 동일 구조(answer + sources)."""
    answer: str = Field(
        ..., 
        description="AI 에이전트가 생성한 마크다운 형식의 답변 텍스트", 
        examples=["CRISPR-Cas9 기법은 유도 RNA(gRNA)를 사용하여 특정 DNA 시퀀스를 절단하는 기술입니다..."]
    )
    sources: list[dict] = Field(
        default_factory=list, 
        description="RAG 파이프라인이 검색하여 참고한 원본 논문 출처 목록", 
        examples=[[{
            "arxiv_id": "2401.56789", 
            "title": "Advances in CRISPR-Cas9 Gene Editing", 
            "summary": "This paper reviews recent structural developments in Cas9 targeting efficiency."
        }]]
    )


class ChatMessageResponseWrapper(SuccessResponse):
    """메시지 전송 응답 래퍼: data = ChatMessageResponse."""
    data: ChatMessageResponse = Field(
        ..., 
        description="AI 대화 응답 및 검색 출처 결과 본문"
    )


class ChatHistoryItem(BaseDTO):
    """대화 내역 1건. role(user/assistant)과 content로 구성된다."""
    role: str = Field(
        ..., 
        description="대화 참여자의 역할 (user: 사용자, assistant: AI 에이전트)", 
        examples=["user"]
    )
    content: str = Field(
        ..., 
        description="대화 텍스트 본문", 
        examples=["CRISPR-Cas9 유전자 편집 기법의 최신 동향을 알려줘."]
    )
    sources: list[dict] = Field(
        default_factory=list, 
        description="AI 에이전트 답변의 경우 근거가 된 논문 출처 목록 (사용자 메시지인 경우 빈 배열)", 
        examples=[[]]
    )


class ChatHistoryResponseWrapper(SuccessResponse):
    """대화 내역 응답 래퍼: data = 대화 내역 리스트."""
    data: list[ChatHistoryItem] = Field(
        ..., 
        description="누적된 전체 대화 히스토리 리스트"
    )
