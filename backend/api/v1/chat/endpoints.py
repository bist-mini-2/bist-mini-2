import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.common.auth import LoginCheckDep, verify_access_token
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
from api.v1.chat.services import ChatServiceDep
from api.v1.chat.multi_agent.supervisor import ChatMultiAgentSupervisorDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["논문 대화 에이전트"], dependencies=[Depends(verify_access_token)])


@router.post("/sessions", summary="신규 대화 세션 생성 API")
async def create_session(
    user: LoginCheckDep,
    request: ChatSessionCreateRequest,
    service: ChatServiceDep,
) -> ChatSessionResponseWrapper:
    """지정된 회원 고유 식별자(mid)와 요청 제목을 기반으로 신규 채팅 세션방을 데이터베이스에 생성합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        request (ChatSessionCreateRequest): 새 채팅방의 제목 정보가 담긴 DTO.
        service (ChatServiceDep): 채팅방 생성 비즈니스 로직을 처리하는 서비스 의존성.

    Returns:
        ChatSessionResponseWrapper: 생성된 채팅방 고유 식별자(session_id)와 세부 메타 정보를 반환.
    """
    chat_session_entity = await service.create_session(user["sub"], request.title)
    return ChatSessionResponseWrapper(
        data=ChatSessionResponse.model_validate(chat_session_entity)
    )


@router.get("/sessions", summary="사용자 소유 대화 세션 목록 조회 API")
async def list_sessions(
    user: LoginCheckDep,
    service: ChatServiceDep,
) -> ChatSessionListResponseWrapper:
    """현재 인증 완료되어 로그인 상태인 유저가 개설했던 모든 채팅 세션 리스트를 최근 생성 시간 순으로 조회합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        service (ChatServiceDep): 채팅방 목록 조회를 전담하는 서비스 의존성.

    Returns:
        ChatSessionListResponseWrapper: 소유하고 있는 전체 채팅 세션 리스트 DTO 객체.
    """
    sessions = await service.list_sessions(user["sub"])
    return ChatSessionListResponseWrapper(
        data=[ChatSessionResponse.model_validate(s) for s in sessions]
    )


@router.delete("/sessions/{session_id}", summary="대화 세션 영구 삭제 API")
async def delete_session(
    user: LoginCheckDep,
    session_id: str,
    service: ChatServiceDep,
) -> SuccessResponse:
    """지정된 고유 채팅 세션방(session_id)의 메타데이터 정보 및 pgvector 대화 히스토리 전체를 데이터베이스에서 소거합니다. (소유자 본인만 가능)

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 삭제할 대상 채팅방의 UUID 고유 식별자.
        service (ChatServiceDep): 채팅방 소거를 처리하는 서비스 의존성.

    Returns:
        SuccessResponse: 성공 완료 안내 메시지를 담은 성공 응답 객체.
    """
    await service.delete_session(user["sub"], session_id)
    return SuccessResponse(
        data={"message": f"삭제된 채팅방 ID: {session_id}"}
    )

@router.patch("/sessions/{session_id}", summary="대화 세션 제목 수정 API")
async def rename_session(
    user: LoginCheckDep,
    session_id: str,
    request: ChatSessionUpdateRequest,
    service: ChatServiceDep,
) -> ChatSessionResponseWrapper:
    """지정된 채팅 세션방(session_id)의 방 제목을 새로운 텍스트로 수정 업데이트합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 이름을 변경할 대상 채팅방의 UUID 고유 식별자.
        request (ChatSessionUpdateRequest): 변경 적용할 새로운 방 제목이 들어있는 요청 DTO.
        service (ChatServiceDep): 제목 수정을 담당하는 서비스 의존성.

    Returns:
        ChatSessionResponseWrapper: 변경 반영된 채팅방 정보를 포함하는 래퍼 DTO 객체.
    """
    chat_session_entity = await service.rename_session(user["sub"], session_id, request.title)
    return ChatSessionResponseWrapper(
        data=ChatSessionResponse.model_validate(chat_session_entity)
    )


@router.post("/sessions/{session_id}/messages", summary="일반 대화 메시지 전송 및 답변 생성 API")
async def send_message(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    service: ChatServiceDep,
) -> ChatMessageResponseWrapper:
    """지정된 채팅 세션방(session_id)을 기반으로 RAG 파이프라인(생명공학, 천문학, CS 등) 논문 검색을 거쳐 완성형 AI 답변을 즉시 반환합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 메시지를 기록하고 참고할 타겟 채팅방의 고유 UUID 식별자.
        request (ChatMessageRequest): 유저가 입력한 대화 메시지 텍스트 요청 DTO.
        service (ChatServiceDep): RAG 에이전트를 수행하고 비즈니스 흐름을 조율하는 서비스 의존성.

    Returns:
        ChatMessageResponseWrapper: AI 가 작성한 최종 설명(answer) 및 참고한 논문 정보(sources) 목록.
    """
    result = await service.send_message(user["sub"], session_id, request.message)
    return ChatMessageResponseWrapper(
        data=ChatMessageResponse(answer=result["answer"], sources=result["sources"])
    )


@router.post("/sessions/{session_id}/messages/multi", summary="[1단계 검증용] 멀티 에이전트(비스트리밍) 대화 메시지 전송 API")
async def send_message_multi(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    supervisor: ChatMultiAgentSupervisorDep,
) -> ChatMessageResponseWrapper:
    """1단계 검증용 멀티 에이전트(비스트리밍) 엔드포인트.

    슈퍼바이저 멀티 에이전트(ChatMultiAgentSupervisor)로 질문을 분석·라우팅하여
    논문 검색(paper) 또는 웹 검색(web) 에이전트가 생성한 답변과 출처를 반환한다.
    이번 단계에서는 동작 검증이 목적이므로 대화 저장(checkpointer)·추천 질문·인용
    후처리는 연결하지 않으며, session_id도 서명 일관성을 위해 받기만 하고 저장에는
    사용하지 않는다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 서명 일관성을 위해 경로로 받는 채팅방 식별자(이번 단계 미사용).
        request (ChatMessageRequest): 유저가 입력한 대화 메시지 텍스트 요청 DTO.
        supervisor (ChatMultiAgentSupervisorDep): 멀티 에이전트 라우팅을 수행하는 슈퍼바이저 의존성.

    Returns:
        ChatMessageResponseWrapper: 멀티 에이전트가 생성한 최종 답변(answer)과 논문 출처(sources).
    """
    result = await supervisor.run(request.message)
    return ChatMessageResponseWrapper(
        data=ChatMessageResponse(answer=result["answer"], sources=result["sources"])
    )


@router.post("/sessions/{session_id}/messages/stream", summary="실시간 스트리밍 대화 메시지 전송 API")
async def send_message_stream(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    service: ChatServiceDep,
):
    """채팅방에 메시지를 전송하고, 생성되는 AI 답변 텍스트 마크다운 문자열을 토큰 단위(char/word)로 분할하여 실시간으로 스트리밍(HTTP Chunked Response) 반환합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 대화 스트림을 기록 및 유지할 대상 채팅방의 고유 UUID 식별자.
        request (ChatMessageRequest): 실시간 질의할 사용자 입력 텍스트 요청 DTO.
        service (ChatServiceDep): 실시간 제너레이터를 호출하고 백그라운드에서 논문 출처를 누적 기록하는 서비스 의존성.

    Returns:
        StreamingResponse: 실시간 토큰 텍스트 단위 응답 스트림.
    """
    return StreamingResponse(
        service.send_message_stream(user["sub"], session_id, request.message),
        media_type="text/plain; charset=utf-8",
    )


@router.post("/sessions/{session_id}/messages/multi/stream", summary="[멀티 에이전트] 실시간 스트리밍 대화 메시지 전송 API")
async def send_message_multi_stream(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    service: ChatServiceDep,
):
    """슈퍼바이저 멀티 에이전트로 질문을 라우팅(논문/웹)하여 답변을 토큰 단위로 스트리밍합니다.

    analysis 에이전트가 질문을 논문(paper)/웹(web)으로 분류한 뒤, 선택된 작업 에이전트가
    답변을 실시간 토큰으로 흘려보낸다. 스트림 종료 후 검색 출처와 추천 후속 질문을 저장한다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 대화 스트림을 기록 및 유지할 대상 채팅방의 고유 UUID 식별자(=thread_id).
        request (ChatMessageRequest): 실시간 질의할 사용자 입력 텍스트 및 선택적 이미지 DTO.
        service (ChatServiceDep): 멀티 에이전트 스트리밍과 출처·추천 저장을 조율하는 서비스 의존성.

    Returns:
        StreamingResponse: status/token/route/image_analysis 이벤트(JSON 라인) 실시간 응답 스트림.
    """
    return StreamingResponse(
        service.send_message_multi_stream(user["sub"], session_id, request.message, request.image),
        media_type="text/plain; charset=utf-8",
    )


@router.get("/sessions/{session_id}/messages", summary="대화 세션 내 모든 메시지 내역 조회 API")
async def get_messages(
    user: LoginCheckDep,
    session_id: str,
    service: ChatServiceDep,
) -> ChatHistoryResponseWrapper:
    """대상 채팅방에서 주고받았던 모든 대화 히스토리 및 각 메시지별 결합되었던 논문 출처 목록을 순서대로 조회합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 대화 내용을 조회할 대상 채팅방의 UUID 고유 식별자.
        service (ChatServiceDep): 대화 내역 조회를 처리하는 서비스 의존성.

    Returns:
        ChatHistoryResponseWrapper: 대화 역할(human/ai), 내용, 출처 목록 정보 배열이 포함된 성공 래퍼 DTO.
    """
    history = await service.get_messages(user["sub"], session_id)
    return ChatHistoryResponseWrapper(
        data=[ChatHistoryItem(**item) for item in history]
    )


@router.post("/sessions/{session_id}/generate-title", summary="대화 맥락 기반 세션 타이틀 요약 생성 API")
async def generate_title(
    user: LoginCheckDep,
    session_id: str,
    request: ChatMessageRequest,
    service: ChatServiceDep,
) -> SuccessResponse:
    """사용자가 처음 던진 질문의 맥락을 LLM으로 자동 요약하여 6~20자의 간결한 한국어 채팅방 타이틀로 가공하고 이를 방의 새 제목으로 자동 업데이트합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 유저의 JWT 페이로드 정보.
        session_id (str): 제목을 자동 설정할 대상 채팅방의 UUID 고유 식별자.
        request (ChatMessageRequest): 첫 질문이 기록된 질의 내용 DTO.
        service (ChatServiceDep): 제목 자동 갱신 처리를 담당하는 서비스 의존성.

    Returns:
        SuccessResponse: 새로 정해진 한국어 채팅방 제목 데이터를 반환.
    """
    title = await service.generate_and_set_title(user["sub"], session_id, request.message)
    return SuccessResponse(data={"title": title})