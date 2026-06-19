import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from api.common.auth import LoginCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.chat.models import (
    ChatSessionCreateRequest,
    ChatSessionUpdateRequest,
    ChatSessionResponse,
    ChatSessionResponseWrapper,
    ChatSessionListResponseWrapper,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessageResponseWrapper,
    ChatHistoryItem,
    ChatHistoryResponseWrapper,
)
from api.v1.chat.service import ChatServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions")
async def create_session(
    user: LoginCheckDep,
    request: ChatSessionCreateRequest,
    service: ChatServiceDep,
) -> ChatSessionResponseWrapper:
    """새로운 채팅방을 생성합니다."""
    chat_session_entity = await service.create_session(user["sub"], request.title)
    return ChatSessionResponseWrapper(
        data=ChatSessionResponse.model_validate(chat_session_entity)
    )


@router.get("/sessions")
async def list_sessions(
    user: LoginCheckDep,
    service: ChatServiceDep,
) -> ChatSessionListResponseWrapper:
    """현재 로그인한 사용자의 채팅방 목록을 조회합니다."""
    sessions = await service.list_sessions(user["sub"])
    return ChatSessionListResponseWrapper(
        data=[ChatSessionResponse.model_validate(s) for s in sessions]
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    user: LoginCheckDep,
    session_id: str,
    service: ChatServiceDep,
) -> SuccessResponse:
    """채팅방을 삭제합니다(대화 기록 포함)."""
    await service.delete_session(user["sub"], session_id)
    return SuccessResponse(
        data={"message": f"삭제된 채팅방 ID: {session_id}"}
    )

@router.patch("/sessions/{session_id}")
async def rename_session(
    user: LoginCheckDep,
    session_id: str,
    request: ChatSessionUpdateRequest,
    service: ChatServiceDep,
) -> ChatSessionResponseWrapper:
    """채팅방 제목을 변경합니다."""
    chat_session_entity = await service.rename_session(user["sub"], session_id, request.title)
    return ChatSessionResponseWrapper(
        data=ChatSessionResponse.model_validate(chat_session_entity)
    )


@router.post("/sessions/{session_id}/messages")
async def send_message(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    service: ChatServiceDep,
) -> ChatMessageResponseWrapper:
    """채팅방에 메시지를 보내고 RAG 기반 답변을 받습니다(대화 기록 자동 저장)."""
    result = await service.send_message(user["sub"], session_id, request.message)
    return ChatMessageResponseWrapper(
        data=ChatMessageResponse(answer=result["answer"], sources=result["sources"])
    )


@router.post("/sessions/{session_id}/messages/stream")
async def send_message_stream(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    service: ChatServiceDep,
):
    """채팅방에 메시지를 보내고 답변을 토큰 단위로 스트리밍합니다(타이핑 효과).

    비스트리밍 POST /messages는 그대로 두고, 스트리밍 경로를 별도로 추가한 것이다.
    출처(sources)는 스트리밍 종료 후 state에 저장되므로, 프론트는 스트리밍이 끝난 뒤
    GET /messages로 출처까지 함께 다시 조회한다.
    """
    return StreamingResponse(
        service.send_message_stream(user["sub"], session_id, request.message),
        media_type="text/plain; charset=utf-8",
    )


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    user: LoginCheckDep,
    session_id: str,
    service: ChatServiceDep,
) -> ChatHistoryResponseWrapper:
    """채팅방의 대화 내역을 순서대로 조회합니다."""
    history = await service.get_messages(user["sub"], session_id)
    return ChatHistoryResponseWrapper(
        data=[ChatHistoryItem(**item) for item in history]
    )


@router.post("/sessions/{session_id}/generate-title")
async def generate_title(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    service: ChatServiceDep,
) -> SuccessResponse:
    """첫 질문을 바탕으로 AI가 채팅방 제목을 생성하고 적용합니다."""
    title = await service.generate_and_set_title(user["sub"], session_id, request.message)
    return SuccessResponse(data={"title": title})