"""사용자 정의 Gem 에이전트 생성, 수정 및 대화 처리를 담당하는 비즈니스 서비스 모듈입니다."""

import logging
import json
import uuid
from typing import Annotated
from fastapi import Depends
from api.common.exceptions import BusinessException
from api.v1.gems.dao import GemDaoDep
from api.v1.gems.entity import GemEntity
from api.v1.gems.gem_agent import GemAgentDep

VALID_SOURCES = {"bio", "cs", "astronomy"}


class GemService:
    """Gem 생성/조회/삭제 및 Gem 대화 처리 비즈니스 로직을 담당합니다."""

    def __init__(self, gem_dao: GemDaoDep, gem_agent: GemAgentDep) -> None:
        """GemService의 인스턴스를 초기화하고 Gem DAO 및 Agent 의존성을 주입합니다.

        Args:
            gem_dao (GemDaoDep): Gem 데이터 액세스 객체.
            gem_agent (GemAgentDep): 멀티 도메인 RAG 및 프롬프트를 처리하는 에이전트 인스턴스.
        """
        self.logger = logging.getLogger(f"{__name__}.GemService")
        self.gem_dao = gem_dao
        self.gem_agent = gem_agent

    async def create_gem(self, member_id: str, name: str, db_sources: list[str], system_prompt: str) -> GemEntity:
        """새 Gem을 생성하고 DB에 저장한다.

        Args:
            member_id (str): 소유자 ID.
            name (str): Gem 이름.
            db_sources (list[str]): RAG DB 소스 목록 (bio/cs/astronomy).
            system_prompt (str): Gem 페르소나 시스템 프롬프트.

        Returns:
            GemEntity: 저장된 Gem 엔티티.

        Raises:
            BusinessException: 유효하지 않은 db_sources가 포함된 경우.
        """
        invalid = set(db_sources) - VALID_SOURCES
        if invalid:
            raise BusinessException(f"유효하지 않은 db_sources: {invalid}. 허용 값: {VALID_SOURCES}")

        gem_entity = GemEntity(
            gem_id=str(uuid.uuid4()),
            member_id=member_id,
            name=name,
            db_sources=",".join(db_sources),
            system_prompt=system_prompt,
        )
        return await self.gem_dao.insert(gem_entity)

    async def list_gems(self, member_id: str) -> list[GemEntity]:
        """사용자가 소유한 Gem 목록을 최신순으로 반환한다.

        Args:
            member_id (str): 조회할 사용자 ID.

        Returns:
            list[GemEntity]: Gem 엔티티 목록.
        """
        return await self.gem_dao.select_by_member(member_id)

    async def _get_owned_gem(self, member_id: str, gem_id: str) -> GemEntity:
        """Gem을 조회하고 현재 사용자가 소유자인지 검증한다.

        Args:
            member_id (str): 요청 사용자 ID.
            gem_id (str): 조회할 Gem ID.

        Returns:
            GemEntity: 검증된 Gem 엔티티.

        Raises:
            BusinessException: Gem이 없거나 소유자가 다른 경우.
        """
        gem = await self.gem_dao.select_by_id(gem_id)
        if not gem:
            raise BusinessException(f"존재하지 않는 Gem: {gem_id}")
        if gem.member_id != member_id:
            raise BusinessException("해당 Gem에 대한 권한이 없습니다.")
        return gem

    async def update_gem(
        self,
        member_id: str,
        gem_id: str,
        name: str | None,
        db_sources: list[str] | None,
        system_prompt: str | None,
    ) -> GemEntity:
        """Gem 메타데이터를 수정한다. 전달된 필드만 업데이트한다(Partial Update).

        Args:
            member_id (str): 요청 사용자 ID.
            gem_id (str): 수정할 Gem ID.
            name (str | None): 새 이름 (None이면 변경 없음).
            db_sources (list[str] | None): 새 RAG 소스 목록 (None이면 변경 없음).
            system_prompt (str | None): 새 시스템 프롬프트 (None이면 변경 없음).

        Returns:
            GemEntity: 수정된 Gem 엔티티.

        Raises:
            BusinessException: 소유자가 다르거나 유효하지 않은 db_sources인 경우.
        """
        gem = await self._get_owned_gem(member_id, gem_id)

        if db_sources is not None:
            invalid = set(db_sources) - VALID_SOURCES
            if invalid:
                raise BusinessException(f"유효하지 않은 db_sources: {invalid}. 허용 값: {VALID_SOURCES}")
            gem.db_sources = ",".join(db_sources)

        if name is not None:
            gem.name = name
        if system_prompt is not None:
            gem.system_prompt = system_prompt

        return await self.gem_dao.update(gem)

    async def delete_gem(self, member_id: str, gem_id: str) -> None:
        """Gem을 삭제한다(메타데이터 + 연결된 모든 대화 기록 제거). 소유자만 가능.

        Args:
            member_id (str): 요청 사용자 ID.
            gem_id (str): 삭제할 Gem ID.
        """
        await self._get_owned_gem(member_id, gem_id)
        await self.gem_dao.delete(gem_id)

    async def send_message(self, member_id: str, gem_id: str, thread_id: str, message: str) -> dict:
        """Gem에 메시지를 보내 RAG 기반 답변을 받는다. 소유자만 가능.

        Args:
            member_id (str): 요청 사용자 ID.
            gem_id (str): 대화할 Gem ID.
            thread_id (str): 대화 스레드 ID.
            message (str): 사용자 입력 메시지.

        Returns:
            dict: answer와 sources를 포함한 딕셔너리.
        """
        gem = await self._get_owned_gem(member_id, gem_id)
        db_sources = gem.db_sources.split(",")
        return await self.gem_agent.run(message, thread_id, db_sources, gem.system_prompt)

    async def get_messages(self, member_id: str, gem_id: str, thread_id: str) -> list[dict]:
        """Gem 대화 스레드의 대화 내역을 반환한다. 소유자만 가능.

        Args:
            member_id (str): 요청 사용자 ID.
            gem_id (str): 조회할 Gem ID.
            thread_id (str): 조회할 대화 스레드 ID.

        Returns:
            list[dict]: [{role, content}] 형식의 대화 내역.
        """
        gem = await self._get_owned_gem(member_id, gem_id)
        db_sources = gem.db_sources.split(",")
        return await self.gem_agent.get_history(thread_id, db_sources, gem.system_prompt)


GemServiceDep = Annotated[GemService, Depends(GemService)]
