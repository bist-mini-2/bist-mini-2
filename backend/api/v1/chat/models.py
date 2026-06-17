from datetime import datetime
from typing import Annotated
from pydantic import Field
from api.database.config.dto_base import BaseDTO, SuccessResponse


class ChatSessionCreateRequest(BaseDTO):
    """채팅방 생성 요청 스키마. 방 제목을 입력받는다."""
    title: Annotated[str, Field(min_length=1, max_length=100)]

class ChatSessionUpdateRequest(BaseDTO):
    """채팅방 제목 수정 요청 DTO."""
    title: str

class ChatSessionResponse(BaseDTO):
    """채팅방(세션) 단건 응답 스키마."""
    session_id: str
    title: str
    created_at: datetime


class ChatSessionListResponseWrapper(SuccessResponse):
    """채팅방 목록 응답 래퍼: data = 채팅방 리스트."""
    data: list[ChatSessionResponse]


class ChatSessionResponseWrapper(SuccessResponse):
    """채팅방 단건 응답 래퍼: data = 채팅방."""
    data: ChatSessionResponse


class ChatMessageRequest(BaseDTO):
    """채팅방 메시지 전송 요청 스키마."""
    message: str


class ChatMessageResponse(BaseDTO):
    """RAG 답변 본문. bio RAG와 동일 구조(answer + sources)."""
    answer: str
    sources: list[dict]


class ChatMessageResponseWrapper(SuccessResponse):
    """메시지 전송 응답 래퍼: data = ChatMessageResponse."""
    data: ChatMessageResponse


class ChatHistoryItem(BaseDTO):
    """대화 내역 1건. role(user/assistant)과 content로 구성된다."""
    role: str
    content: str


class ChatHistoryResponseWrapper(SuccessResponse):
    """대화 내역 응답 래퍼: data = 대화 내역 리스트."""
    data: list[ChatHistoryItem]
