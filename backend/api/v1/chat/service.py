import logging
import uuid
from typing import Annotated
from fastapi import Depends
from api.common.exceptions import BusinessException
from api.v1.chat.chat_agent import ChatAgentDep
from api.v1.chat.dao import ChatSessionDaoDep
from api.v1.chat.entity import ChatSessionEntity
from api.v1.chat.dao import ChatSessionDaoDep


class ChatService:
    """채팅방 관리(생성/조회/삭제)와 방 안에서의 대화 처리 비즈니스 로직을 담당합니다."""

    def __init__(self, chat_session_dao: ChatSessionDaoDep, chat_agent: ChatAgentDep) -> None:
        self.logger = logging.getLogger(f"{__name__}.ChatService")
        self.chat_session_dao = chat_session_dao
        self.chat_agent = chat_agent

    async def create_session(self, member_id: str, title: str) -> ChatSessionEntity:
        """사용자의 새 채팅방을 생성한다(UUID로 session_id 발급)."""
        self.logger.info("create_session 실행")
        chat_session_entity = ChatSessionEntity(
            session_id=str(uuid.uuid4()),
            member_id=member_id,
            title=title,
        )
        return await self.chat_session_dao.insert(chat_session_entity)

    async def list_sessions(self, member_id: str) -> list[ChatSessionEntity]:
        """사용자가 소유한 채팅방 목록을 최신순으로 반환한다."""
        return await self.chat_session_dao.select_by_member(member_id)

    async def _get_owned_session(self, member_id: str, session_id: str) -> ChatSessionEntity:
        """채팅방을 조회하고 현재 사용자가 소유자인지 검증한다."""
        chat_session_entity = await self.chat_session_dao.select_by_id(session_id)
        if not chat_session_entity:
            raise BusinessException(f"존재하지 않는 채팅방: {session_id}")
        if chat_session_entity.member_id != member_id:
            raise BusinessException("해당 채팅방에 대한 권한이 없습니다.")
        return chat_session_entity

    async def delete_session(self, member_id: str, session_id: str) -> None:
        """채팅방을 삭제한다(메타데이터 + 대화 기록 함께 제거). 소유자만 가능."""
        await self._get_owned_session(member_id, session_id)
        await self.chat_session_dao.delete(session_id)
        await self.chat_agent.clear_history(session_id)

    async def rename_session(self, member_id: str, session_id: str, title: str) -> ChatSessionEntity:
        """채팅방 제목을 변경한다. 소유자만 가능."""
        chat_session_entity = await self._get_owned_session(member_id, session_id)
        await self.chat_session_dao.update_title(session_id, title)
        chat_session_entity.title = title
        return chat_session_entity
    

    async def send_message(self, member_id: str, session_id: str, message: str) -> dict:
        """채팅방에 메시지를 보내 RAG 기반 답변을 받는다(대화 기록 + 출처 저장). 소유자만 가능."""
        await self._get_owned_session(member_id, session_id)
        result = await self.chat_agent.run(message, session_id)

        # 답변의 출처를 영구 저장한다.
        # run() 직후 전체 대화 내역을 세어, 방금 추가된 assistant 메시지의 index를 구한다.
        if result.get("sources"):
            history = await self.chat_agent.get_history(session_id)
            assistant_index = len(history) - 1   # 마지막 메시지(방금 답변)의 index
            await self.chat_session_dao.insert_sources(
                session_id, assistant_index, result["sources"]
            )

        return result

    async def get_messages(self, member_id: str, session_id: str) -> list[dict]:
        """채팅방의 대화 내역을 출처와 함께 순서대로 반환한다. 소유자만 가능."""
        await self._get_owned_session(member_id, session_id)
        history = await self.chat_agent.get_history(session_id)

        # 저장된 출처를 message_index 기준으로 묶어 각 메시지에 붙인다.
        sources = await self.chat_session_dao.select_sources_by_session(session_id)
        sources_by_index = {}
        for s in sources:
            sources_by_index.setdefault(s.message_index, []).append(
                {"arxiv_id": s.arxiv_id, "title": s.title}
            )

        for idx, msg in enumerate(history):
            msg["sources"] = sources_by_index.get(idx, [])

        return history


ChatServiceDep = Annotated[ChatService, Depends(ChatService)]
