import asyncio
import json
import logging
from typing import Annotated, AsyncGenerator
from fastapi import Depends, Request

from api.v1.notification.notifier import notification_broadcaster

logger = logging.getLogger(__name__)


class NotificationService:
    """실시간 SSE 알림 스트리밍 제너레이터 공급 및 알림 관련 비즈니스 로직을 처리하는 서비스 클래스입니다."""

    async def stream_notifications(self, request: Request, mid: str) -> AsyncGenerator[str, None]:
        """구독 중인 클라이언트 리스너 큐로부터 이벤트를 읽어와 SSE 문자열 스트림으로 양방향 전달하는 제너레이터입니다.

        Args:
            request (Request): FastAPI 요청 객체.
            mid (str): 현재 인증된 사용자의 식별자 ID.

        Yields:
            AsyncGenerator[str, None]: SSE 형식의 데이터 문자열 스트림.
        """
        queue = notification_broadcaster.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    logger.info(f"SSE client disconnected for user: {mid}")
                    break
                try:
                    # 1.0초 타임아웃 대기로 리스너가 살아있음을 보장하며 신규 알림 수신
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    # 수신된 메시지의 수신자 식별자(mid)가 존재하고, 현재 로그인 사용자 정보와 다르면 필터링
                    event_mid = message.get("mid")
                    if event_mid and event_mid != mid:
                        continue
                    
                    content = f"data: {json.dumps(message)}\n\n"
                    if isinstance(content, str) and content:
                        yield content
                except asyncio.TimeoutError:
                    # keep-alive 데이터를 보내 Nginx 등의 프록시 타임아웃 방지
                    content = ": keep-alive\n\n"
                    if isinstance(content, str) and content:
                        yield content
        finally:
            notification_broadcaster.unsubscribe(queue)


# Annotated 의존성 주입을 위한 타입 Alias 선언
NotificationServiceDep = Annotated[NotificationService, Depends(NotificationService)]
