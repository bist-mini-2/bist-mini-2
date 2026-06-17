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
