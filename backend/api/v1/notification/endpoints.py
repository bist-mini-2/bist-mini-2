import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse

from api.common.auth import LoginCheckDep, verify_access_token
from api.v1.notification.services import NotificationServiceDep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notification", tags=["실시간 알림"], dependencies=[Depends(verify_access_token)])


@router.get(
    "/stream",
    summary="실시간 SSE 통합 푸시 알림 스트림 API",
    include_in_schema=False
)
async def stream_notifications(
    request: Request,
    service: NotificationServiceDep,
    current_user: LoginCheckDep
):
    """실시간으로 사용자별 전송되는 통합 푸시 알림 이벤트를 SSE(Server-Sent Events) 커넥션을 맺어 스트리밍합니다.

    Args:
        request (Request): 클라이언트와의 TCP 접속 유지 및 해제 감지를 수행하는 FastAPI Request 객체.
        service (NotificationServiceDep): 실시간 알림 큐를 구독(subscribe) 처리하는 비즈니스 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        StreamingResponse: text/event-stream 규격의 실시간 푸시 스트림 응답.
    """
    mid = current_user["sub"]
    logger.info(f"SSE stream initiated for user: {mid}")
    return StreamingResponse(
        service.stream_notifications(request, mid),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


from api.database.config.dto_base import SuccessResponse
from api.v1.notification.models import NotificationDTO
from typing import List


@router.get(
    "",
    response_model=SuccessResponse,
    summary="알림 목록 조회 API"
)
async def list_notifications(
    service: NotificationServiceDep,
    current_user: LoginCheckDep
):
    """현재 사용자에게 도달한 실시간 알림 및 읽지 않고 오프라인 상태일 때 쌓였던 알림 전체 목록을 최근 순으로 반환합니다.

    Args:
        service (NotificationServiceDep): 사용자의 알림 엔티티 조회를 수행하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: DTO 포맷팅이 완료된 사용자의 알림 데이터 리스트 배열 정보.
    """
    mid = current_user["sub"]
    notifs = await service.list_notifications(mid)
    # DTO 변환 수행
    dto_list = [NotificationDTO.model_validate(n) for n in notifs]
    return SuccessResponse(data=dto_list)


@router.put(
    "/{id}/read",
    response_model=SuccessResponse,
    summary="개별 알림 읽음 처리 API"
)
async def mark_as_read(
    id: str,
    service: NotificationServiceDep,
    current_user: LoginCheckDep
):
    """사용자에게 도달한 특정 개별 알림 항목(id)의 상태를 '읽음(is_read=True)' 상태로 업데이트합니다.

    Args:
        id (str): 읽음 표시 적용할 알림의 UUID 고유 식별자.
        service (NotificationServiceDep): 읽음 상태 변경을 트랜잭션 처리하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 성공 완료 여부 데이터를 반환.
    """
    mid = current_user["sub"]
    success = await service.mark_as_read(id, mid)
    return SuccessResponse(data={"success": success})


@router.put(
    "/read-all",
    response_model=SuccessResponse,
    summary="전체 알림 읽음 처리 API"
)
async def mark_all_as_read(
    service: NotificationServiceDep,
    current_user: LoginCheckDep
):
    """현재 로그인한 유저에게 유입되었던 모든 미읽음 상태의 알림들을 일괄로 '읽음' 처리합니다.

    Args:
        service (NotificationServiceDep): 알림 일괄 수정을 담당하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 성공 반영 여부 데이터를 반환.
    """
    mid = current_user["sub"]
    await service.mark_all_as_read(mid)
    return SuccessResponse(data={"success": True})


@router.delete(
    "/{id}",
    response_model=SuccessResponse,
    summary="개별 알림 삭제 API"
)
async def delete_notification(
    id: str,
    service: NotificationServiceDep,
    current_user: LoginCheckDep
):
    """사용자가 수신했던 특정 개별 알림 데이터(id)를 데이터베이스에서 영구적으로 소거합니다.

    Args:
        id (str): 삭제할 특정 알림의 고유 UUID 식별자.
        service (NotificationServiceDep): 알림 삭제를 트랜잭션 처리하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 성공적으로 소거되었는지 여부 데이터를 반환.
    """
    mid = current_user["sub"]
    success = await service.delete_notification(id, mid)
    return SuccessResponse(data={"success": success})


@router.delete(
    "",
    response_model=SuccessResponse,
    summary="전체 알림 삭제 API"
)
async def delete_all_notifications(
    service: NotificationServiceDep,
    current_user: LoginCheckDep
):
    """현재 로그인 유저에게 수신 누적되었던 모든 알림 이력 데이터를 일괄적으로 데이터베이스에서 영구 제거합니다.

    Args:
        service (NotificationServiceDep): 알림 전체 일괄 삭제를 처리하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 일괄 삭제 완료 반영 상태를 반환.
    """
    mid = current_user["sub"]
    await service.delete_all_notifications(mid)
    return SuccessResponse(data={"success": True})

