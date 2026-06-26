"""채팅 세션 데이터베이스 액세스를 처리하는 DAO 모듈입니다."""

import logging
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select, text
from api.database.config.dbsession import OrmSessionDep
from api.v1.chat.entity import ChatSessionEntity, ChatSourceEntity, ChatSuggestionEntity


class ChatSessionDao:
    """chat_session 테이블에 대한 ORM 작업을 수행하는 데이터 액세스 객체(DAO)입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        """ChatSessionDao의 인스턴스를 초기화하고 ORM 세션을 주입합니다.

        Args:
            orm_session (OrmSessionDep): 데이터베이스 ORM 세션 의존성.
        """
        self.logger = logging.getLogger(f"{__name__}.ChatSessionDao")
        self.orm_session = orm_session

    async def insert(self, chat_session_entity: ChatSessionEntity) -> ChatSessionEntity:
        """새로운 채팅방(세션) 메타데이터를 저장합니다.

        Args:
            chat_session_entity (ChatSessionEntity): 추가할 신규 채팅 세션 엔티티.

        Returns:
            ChatSessionEntity: 저장 및 영속화가 완료된 채팅 세션 엔티티.
        """
        self.logger.info("insert 실행")
        self.orm_session.add(chat_session_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(chat_session_entity)
        return chat_session_entity

    async def select_by_member(self, member_id: str) -> list[ChatSessionEntity]:
        """특정 사용자가 소유한 채팅방 목록을 최신순(created_at desc)으로 조회합니다.

        Args:
            member_id (str): 조회를 요청한 회원의 아이디.

        Returns:
            list[ChatSessionEntity]: 정렬되어 조회된 채팅 세션 엔티티 목록.
        """
        result = await self.orm_session.execute(
            select(ChatSessionEntity)
            .where(ChatSessionEntity.member_id == member_id)
            .order_by(ChatSessionEntity.created_at.desc())
        )
        return list(result.scalars().all())

    async def select_by_id(self, session_id: str) -> ChatSessionEntity | None:
        """채팅방 ID로 단건 메타데이터를 조회합니다.

        Args:
            session_id (str): 조회 대상 채팅방 세션 ID.

        Returns:
            ChatSessionEntity | None: 조회된 세션 엔티티 또는 존재하지 않을 경우 None.
        """
        return await self.orm_session.get(ChatSessionEntity, session_id)

    async def delete(self, session_id: str):
        """채팅방(세션) 메타데이터를 ID 기준으로 삭제합니다.

        Args:
            session_id (str): 삭제할 채팅 세션 ID.
        """
        await self.orm_session.execute(
            text("DELETE FROM chat_session WHERE session_id = :session_id"),
            {"session_id": session_id},
        )
    
    async def update_title(self, session_id: str, title: str) -> None:
        """채팅방 제목을 수정합니다.

        Args:
            session_id (str): 수정할 채팅 세션 ID.
            title (str): 반영할 새로운 방 제목.
        """
        chat_session_entity = await self.orm_session.get(ChatSessionEntity, session_id)
        if chat_session_entity:
            chat_session_entity.title = title
            await self.orm_session.flush()


    async def insert_sources(self, session_id: str, message_index: int, sources: list[dict]) -> None:
        """특정 메시지의 출처 목록을 저장합니다.

        Args:
            session_id (str): 대상 채팅 세션 ID.
            message_index (int): 대화 내역 상에서의 어시스턴트 메시지 인덱스.
            sources (list[dict]): 저장할 출처 정보들의 리스트.
        """
        for src in sources:
            self.orm_session.add(ChatSourceEntity(
                session_id=session_id,
                message_index=message_index,
                arxiv_id=src["arxiv_id"],
                title=src["title"],
                summary=src.get("summary")
            ))
        await self.orm_session.flush()

    async def select_sources_by_session(self, session_id: str) -> list[ChatSourceEntity]:
        """특정 방의 모든 출처를 조회합니다 (메시지 index 순).

        Args:
            session_id (str): 대상 채팅 세션 ID.

        Returns:
            list[ChatSourceEntity]: 조회된 출처 정보 엔티티 목록.
        """
        result = await self.orm_session.execute(
            select(ChatSourceEntity)
            .where(ChatSourceEntity.session_id == session_id)
            .order_by(ChatSourceEntity.message_index)
        )
        return list(result.scalars().all())

    async def insert_suggestions(self, session_id: str, message_index: int, questions: list[str]) -> None:
        """특정 메시지의 추천 후속 질문 목록을 저장합니다.

        Args:
            session_id (str): 대상 채팅 세션 ID.
            message_index (int): 대화 내역 상에서의 어시스턴트 메시지 인덱스.
            questions (list[str]): 저장할 추천 질문 문자열 리스트.
        """
        for q in questions:
            self.orm_session.add(ChatSuggestionEntity(
                session_id=session_id,
                message_index=message_index,
                question=q,
            ))
        await self.orm_session.flush()

    async def select_suggestions_by_session(self, session_id: str) -> list[ChatSuggestionEntity]:
        """특정 방의 모든 추천 질문을 조회합니다 (메시지 index 순).

        Args:
            session_id (str): 대상 채팅 세션 ID.

        Returns:
            list[ChatSuggestionEntity]: 조회된 추천 질문 엔티티 목록.
        """
        result = await self.orm_session.execute(
            select(ChatSuggestionEntity)
            .where(ChatSuggestionEntity.session_id == session_id)
            .order_by(ChatSuggestionEntity.message_index)
        )
        return list(result.scalars().all())

    async def commit(self) -> None:
        """세션을 명시적으로 커밋한다.

        StreamingResponse는 요청 의존성의 자동 커밋이 보장되지 않으므로 직접 호출한다.
        """
        await self.orm_session.commit()


ChatSessionDaoDep = Annotated[ChatSessionDao, Depends(ChatSessionDao)]
