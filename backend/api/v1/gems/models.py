from datetime import datetime
from typing import Annotated
from pydantic import Field
from api.database.config.dto_base import BaseDTO, SuccessResponse


class GemCreateRequest(BaseDTO):
    """Gem 생성 요청 스키마."""
    name: Annotated[str, Field(min_length=1, max_length=100)]
    db_sources: Annotated[list[str], Field(min_length=1)]  # ["bio", "cs", "astronomy"] 중 다중 선택
    system_prompt: Annotated[str, Field(min_length=1)]


class GemResponse(BaseDTO):
    """Gem 단건 응답 스키마."""
    gem_id: str
    name: str
    db_sources: list[str]
    system_prompt: str
    created_at: datetime


class GemListResponseWrapper(SuccessResponse):
    """Gem 목록 응답 래퍼."""
    data: list[GemResponse]


class GemResponseWrapper(SuccessResponse):
    """Gem 단건 응답 래퍼."""
    data: GemResponse


class GemUpdateRequest(BaseDTO):
    """Gem 수정 요청 스키마. 전달된 필드만 업데이트한다."""
    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    db_sources: Annotated[list[str], Field(min_length=1)] | None = None
    system_prompt: Annotated[str, Field(min_length=1)] | None = None


class GemChatRequest(BaseDTO):
    """Gem 대화 요청 스키마."""
    thread_id: str
    message: str


class GemChatResponse(BaseDTO):
    """Gem 대화 응답 스키마."""
    answer: str
    sources: list[dict]


class GemChatResponseWrapper(SuccessResponse):
    """Gem 대화 응답 래퍼."""
    data: GemChatResponse
