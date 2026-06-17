import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from api.common.auth import LoginCheckDep
from api.v1.notification.services import NotificationServiceDep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notification", tags=["알림"])


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
    """실시간으로 전역 알림을 SSE(Server-Sent Events) 프로토콜을 이용해 클라이언트로 스트리밍합니다."""
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
    """현재 로그인한 사용자의 실시간 및 오프라인 누적 알림 목록을 반환합니다."""
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
    """특정 알림을 읽음 처리합니다."""
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
    """사용자의 모든 미읽음 알림을 일괄 읽음 처리합니다."""
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
    """특정 알림을 삭제합니다."""
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
    """사용자의 모든 알림을 삭제합니다."""
    mid = current_user["sub"]
    await service.delete_all_notifications(mid)
    return SuccessResponse(data={"success": True})

