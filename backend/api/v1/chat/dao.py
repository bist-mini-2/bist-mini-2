import logging
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select, text
from api.database.config.dbsession import OrmSessionDep
from api.v1.chat.entity import ChatSessionEntity


class ChatSessionDao:
    """chat_session 테이블에 대한 ORM 작업을 수행하는 데이터 액세스 객체(DAO)입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        self.logger = logging.getLogger(f"{__name__}.ChatSessionDao")
        self.orm_session = orm_session

    async def insert(self, chat_session_entity: ChatSessionEntity) -> ChatSessionEntity:
        """새로운 채팅방(세션) 메타데이터를 저장합니다."""
        self.logger.info("insert 실행")
        self.orm_session.add(chat_session_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(chat_session_entity)
        return chat_session_entity

    async def select_by_member(self, member_id: str) -> list[ChatSessionEntity]:
        """특정 사용자가 소유한 채팅방 목록을 최신순(created_at desc)으로 조회합니다."""
        result = await self.orm_session.execute(
            select(ChatSessionEntity)
            .where(ChatSessionEntity.member_id == member_id)
            .order_by(ChatSessionEntity.created_at.desc())
        )
        return list(result.scalars().all())

    async def select_by_id(self, session_id: str) -> ChatSessionEntity | None:
        """채팅방 ID로 단건 메타데이터를 조회합니다."""
        return await self.orm_session.get(ChatSessionEntity, session_id)

    async def delete(self, session_id: str):
        """채팅방(세션) 메타데이터를 ID 기준으로 삭제합니다."""
        await self.orm_session.execute(
            text("DELETE FROM chat_session WHERE session_id = :session_id"),
            {"session_id": session_id},
        )


ChatSessionDaoDep = Annotated[ChatSessionDao, Depends(ChatSessionDao)]
