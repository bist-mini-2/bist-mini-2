"""실시간 및 오프라인 누적 알림 데이터의 DB 상태 관리를 수행하는 DAO 모듈입니다."""

import logging
from typing import Annotated, List, Optional
from fastapi import Depends
from sqlalchemy import select, update, delete
from api.database.config.dbsession import OrmSessionDep
from api.v1.notification.entity import NotificationEntity


class NotificationDao:
    """실시간 및 오프라인 누적 알림 데이터의 DB 상태 관리를 수행하는 DAO 클래스입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        """NotificationDao의 인스턴스를 초기화하고 ORM 세션을 주입합니다.

        Args:
            orm_session (OrmSessionDep): 데이터베이스 ORM 세션 의존성.
        """
        self.logger = logging.getLogger(f"{__name__}.NotificationDao")
        self.orm_session = orm_session

    async def create_notification(
        self, id: str, mid: str, title: str, message: str, type: str, task_id: Optional[str] = None
    ) -> NotificationEntity:
        """새로운 알림을 생성하여 DB에 영구 저장합니다."""
        self.logger.info(f"create_notification: {id} (mid={mid}, title={title})")
        notification = NotificationEntity(
            id=id,
            mid=mid,
            title=title,
            message=message,
            type=type,
            task_id=task_id,
            read=False
        )
        self.orm_session.add(notification)
        await self.orm_session.flush()
        return notification

    async def list_notifications(self, mid: str) -> List[NotificationEntity]:
        """사용자의 알림 목록을 최신순(created_at desc)으로 조회합니다."""
        stmt = (
            select(NotificationEntity)
            .where(NotificationEntity.mid == mid)
            .order_by(NotificationEntity.created_at.desc())
        )
        result = await self.orm_session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_read(self, id: str, mid: str) -> bool:
        """특정 알림을 읽음 상태로 표시합니다."""
        stmt = (
            update(NotificationEntity)
            .where(NotificationEntity.id == id, NotificationEntity.mid == mid)
            .values(read=True)
        )
        result = await self.orm_session.execute(stmt)
        return result.rowcount > 0

    async def mark_all_as_read(self, mid: str) -> None:
        """사용자의 모든 미읽음 알림을 읽음 상태로 표시합니다."""
        stmt = (
            update(NotificationEntity)
            .where(NotificationEntity.mid == mid, NotificationEntity.read == False)
            .values(read=True)
        )
        await self.orm_session.execute(stmt)

    async def delete_notification(self, id: str, mid: str) -> bool:
        """특정 알림을 삭제합니다."""
        stmt = (
            delete(NotificationEntity)
            .where(NotificationEntity.id == id, NotificationEntity.mid == mid)
        )
        result = await self.orm_session.execute(stmt)
        return result.rowcount > 0

    async def delete_all_notifications(self, mid: str) -> None:
        """사용자의 모든 알림을 삭제합니다."""
        stmt = delete(NotificationEntity).where(NotificationEntity.mid == mid)
        await self.orm_session.execute(stmt)


NotificationDaoDep = Annotated[NotificationDao, Depends(NotificationDao)]
