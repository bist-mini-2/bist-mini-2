"""채팅 세션 관리 및 RAG 기반 AI 상담 비즈니스 로직을 처리하는 모듈입니다."""

import logging
import json
import uuid
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from api.common.exceptions import BusinessException
from api.v1.chat.chat_agent import ChatAgentDep
from api.v1.chat.dao import ChatSessionDaoDep
from api.v1.chat.entity import ChatSessionEntity


class ChatService:
    """채팅방 관리(생성/조회/삭제)와 방 안에서의 대화 처리 비즈니스 로직을 담당합니다."""

    def __init__(self, chat_session_dao: ChatSessionDaoDep, chat_agent: ChatAgentDep) -> None:
        """ChatService의 인스턴스를 초기화하고 DAO 및 Agent 의존성을 주입합니다.

        Args:
            chat_session_dao (ChatSessionDaoDep): 채팅 세션 데이터 액세스 객체.
            chat_agent (ChatAgentDep): RAG 및 챗봇 인터페이스를 캡슐화한 에이전트 인스턴스.
        """
        self.logger = logging.getLogger(f"{__name__}.ChatService")
        self.chat_session_dao = chat_session_dao
        self.chat_agent = chat_agent

    async def create_session(self, member_id: str, title: str) -> ChatSessionEntity:
        """사용자의 새 채팅방을 생성한다 (UUID로 session_id 발급).

        Args:
            member_id (str): 채팅방을 생성할 회원의 아이디.
            title (str): 채팅방 제목.

        Returns:
            ChatSessionEntity: 데이터베이스에 등록 완료된 신규 채팅 세션 엔티티.
        """
        self.logger.info("create_session 실행")
        chat_session_entity = ChatSessionEntity(
            session_id=str(uuid.uuid4()),
            member_id=member_id,
            title=title,
        )
        return await self.chat_session_dao.insert(chat_session_entity)

    async def list_sessions(self, member_id: str) -> list[ChatSessionEntity]:
        """사용자가 소유한 채팅방 목록을 최신순으로 반환한다.

        Args:
            member_id (str): 조회를 요청한 회원의 아이디.

        Returns:
            list[ChatSessionEntity]: 소유한 채팅 세션 엔티티 리스트.
        """
        return await self.chat_session_dao.select_by_member(member_id)

    async def _get_owned_session(self, member_id: str, session_id: str) -> ChatSessionEntity:
        """채팅방을 조회하고 현재 사용자가 소유자인지 검증한다.

        Args:
            member_id (str): 검증할 회원의 아이디.
            session_id (str): 조회할 채팅방 세션 ID.

        Returns:
            ChatSessionEntity: 검증 완료된 채팅 세션 엔티티 정보.

        Raises:
            BusinessException: 채팅방이 존재하지 않거나 소유 권한F이 없는 경우.
        """
        chat_session_entity = await self.chat_session_dao.select_by_id(session_id)
        if not chat_session_entity:
            raise BusinessException(f"존재하지 않는 채팅방: {session_id}")
        if chat_session_entity.member_id != member_id:
            raise BusinessException("해당 채팅방에 대한 권한이 없습니다.")
        return chat_session_entity

    async def delete_session(self, member_id: str, session_id: str) -> None:
        """채팅방을 삭제한다 (메타데이터 + 대화 기록 함께 제거). 소유자만 가능.

        Args:
            member_id (str): 삭제를 요청한 회원의 아이디.
            session_id (str): 삭제할 채팅 세션 ID.
        """
        await self._get_owned_session(member_id, session_id)
        await self.chat_session_dao.delete(session_id)
        await self.chat_agent.clear_history(session_id)

    async def rename_session(self, member_id: str, session_id: str, title: str) -> ChatSessionEntity:
        """채팅방 제목을 변경한다. 소유자만 가능.

        Args:
            member_id (str): 변경을 요청한 회원의 아이디.
            session_id (str): 제목을 변경할 채팅 세션 ID.
            title (str): 변경할 새로운 제목 텍스트.

        Returns:
            ChatSessionEntity: 제목 변경이 반영된 채팅 세션 엔티티.
        """
        chat_session_entity = await self._get_owned_session(member_id, session_id)
        await self.chat_session_dao.update_title(session_id, title)
        chat_session_entity.title = title
        return chat_session_entity

    async def generate_and_set_title(self, member_id: str, session_id: str, question: str) -> str:
        """첫 질문을 바탕으로 AI가 채팅방 제목을 생성하고 적용한다. 소유자만 가능.

        Args:
            member_id (str): 요청 회원의 아이디.
            session_id (str): 대상 채팅 세션 ID.
            question (str): 방의 첫 질문 텍스트.

        Returns:
            str: 새로이 갱신되어 데이터베이스에 적용된 방 제목 텍스트.
        """
        await self._get_owned_session(member_id, session_id)
        title = await self.chat_agent.generate_title(question)
        await self.chat_session_dao.update_title(session_id, title)
        return title

    async def send_message(self, member_id: str, session_id: str, message: str) -> dict:
        """채팅방에 메시지를 보내 RAG 기반 답변을 받는다 (대화 기록 + 출처 저장). 소유자만 가능.

        Args:
            member_id (str): 요청 회원의 아이디.
            session_id (str): 대상 채팅 세션 ID.
            message (str): 사용자의 입력 질문 텍스트.

        Returns:
            dict: AI 답변 및 문서 출처 정보를 포함하는 딕셔너리.
        """
        await self._get_owned_session(member_id, session_id)
        result = await self.chat_agent.run(message, session_id)

        # 답변의 출처를 영구 저장한다.
        if result.get("sources"):
            history = await self.chat_agent.get_history(session_id)
            assistant_index = len(history) - 1   # 마지막 메시지(방금 답변)의 index
            await self.chat_session_dao.insert_sources(
                session_id, assistant_index, result["sources"]
            )

        return result

    async def send_message_stream(self, member_id: str, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """채팅방에 메시지를 보내 답변을 토큰 단위로 스트리밍한다 (타이핑 효과). 소유자만 가능.

        Args:
            member_id (str): 요청 회원의 아이디.
            session_id (str): 대상 채팅 세션 ID.
            message (str): 사용자의 입력 질문 텍스트.

        Yields:
            str: AI 답변의 각 단어/토큰 조각 문자열.
        """
        await self._get_owned_session(member_id, session_id)

        async for event in self.chat_agent.run_stream(message, session_id):
            yield json.dumps(event, ensure_ascii=False) + "\n"

        # 스트리밍 종료 후 출처 저장 (실패해도 대화에는 영향 없음)
        # 스트리밍 종료 후 출처 + 추천 질문 저장 (실패해도 대화에는 영향 없음)
        try:
            history = await self.chat_agent.get_history(session_id)
            assistant_index = len(history) - 1   # 마지막 메시지(방금 답변)의 index

            # 1) 검색 출처 저장
            sources = await self.chat_agent.get_latest_sources(session_id)
            if sources:
                await self.chat_session_dao.insert_sources(
                    session_id, assistant_index, sources
                )

            # 2) 추천 후속 질문 생성·저장 (방금 질문 + 방금 답변 기반)
            answer = history[-1]["content"] if history else ""
            suggestions = await self.chat_agent.generate_suggestions(message, answer)
            if suggestions:
                await self.chat_session_dao.insert_suggestions(
                    session_id, assistant_index, suggestions
                )

            await self.chat_session_dao.commit()
        except Exception as e:
            self.logger.error(f"스트리밍 출처·추천 저장 실패 (session_id={session_id}): {e}")

    async def get_messages(self, member_id: str, session_id: str) -> list[dict]:
        """채팅방의 대화 내역을 출처와 함께 순서대로 반환한다. 소유자만 가능.

        Args:
            member_id (str): 요청 회원의 아이디.
            session_id (str): 조회 대상 채팅 세션 ID.

        Returns:
            list[dict]: 출처 정보가 임베디드된 채팅 히스토리 메시지 목록.
        """
        await self._get_owned_session(member_id, session_id)
        history = await self.chat_agent.get_history(session_id)

        # 저장된 출처를 message_index 기준으로 묶어 각 메시지에 붙인다.
        sources = await self.chat_session_dao.select_sources_by_session(session_id)
        sources_by_index = {}
        for s in sources:
            sources_by_index.setdefault(s.message_index, []).append(
                {"arxiv_id": s.arxiv_id, "title": s.title, "summary": s.summary or ""}
            )

        # 저장된 추천 질문도 message_index 기준으로 묶는다.
        suggestions = await self.chat_session_dao.select_suggestions_by_session(session_id)
        suggestions_by_index = {}
        for s in suggestions:
            suggestions_by_index.setdefault(s.message_index, []).append(s.question)

        for idx, msg in enumerate(history):
            msg["sources"] = sources_by_index.get(idx, [])
            msg["suggestions"] = suggestions_by_index.get(idx, [])

        return history


ChatServiceDep = Annotated[ChatService, Depends(ChatService)]
