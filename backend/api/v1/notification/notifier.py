import asyncio
import logging
from typing import Set

logger = logging.getLogger(__name__)


class NotificationBroadcaster:
    """비동기 배치 태스크 상태 변경 및 완료 알림 등을 실시간 SSE 채널로 브로드캐스트하는 중앙 인메모리 퍼블리셔입니다."""

    def __init__(self) -> None:
        """NotificationBroadcaster의 인스턴스를 초기화합니다."""
        self._listeners: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        """새로운 클라이언트 리스너를 구독 등록하고 비동기 큐를 반환합니다.

        Returns:
            asyncio.Queue: 이벤트를 수신할 비동기 큐 객체.
        """
        queue = asyncio.Queue()
        self._listeners.add(queue)
        logger.info(f"New client subscribed. Active listeners: {len(self._listeners)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """등록된 클라이언트 비동기 큐의 구독을 해제합니다.

        Args:
            queue (asyncio.Queue): 구독 해제할 큐 객체.
        """
        if queue in self._listeners:
            self._listeners.remove(queue)
            logger.info(f"Client unsubscribed. Active listeners: {len(self._listeners)}")

    async def broadcast(self, message: dict) -> None:
        """구독 중인 모든 클라이언트 리스너 큐에 메시지 이벤트를 비동기 전송합니다.

        Args:
            message (dict): 브로드캐스트할 메시지 데이터 딕셔너리.
        """
        if not self._listeners:
            logger.debug("No listeners subscribed. Skipping broadcast.")
            return
        
        logger.info(f"Broadcasting message to {len(self._listeners)} listeners: {message}")
        # 동시 전송 처리 및 개별 실패 예외 방어
        await asyncio.gather(
            *[queue.put(message) for queue in self._listeners],
            return_exceptions=True
        )


# 전역 싱글톤 인스턴스 정의
notification_broadcaster = NotificationBroadcaster()
