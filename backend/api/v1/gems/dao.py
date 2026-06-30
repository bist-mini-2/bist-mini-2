"""사용자 정의 Gem 에이전트 정보의 데이터베이스 CRUD 작업을 전담하는 DAO 모듈입니다."""

import logging
import uuid
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from api.database.config.dbsession import OrmSessionDep
from api.v1.gems.entity import GemEntity, GemFileEntity


class GemDao:
    """gem 및 gem_file 테이블에 대한 ORM 작업을 수행하는 데이터 액세스 객체(DAO)입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        """GemDao의 인스턴스를 초기화하고 ORM 세션을 주입합니다.

        Args:
            orm_session (OrmSessionDep): 데이터베이스 ORM 세션 의존성.
        """
        self.logger = logging.getLogger(f"{__name__}.GemDao")
        self.orm_session = orm_session

    async def insert(self, gem_entity: GemEntity) -> GemEntity:
        """새로운 Gem을 저장합니다.

        Args:
            gem_entity (GemEntity): 저장할 신규 Gem 엔티티.

        Returns:
            GemEntity: 저장 및 영속화가 완료된 Gem 엔티티.
        """
        self.logger.info("insert 실행")
        self.orm_session.add(gem_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(gem_entity)
        return gem_entity

    async def select_by_member(self, member_id: str) -> list[GemEntity]:
        """특정 사용자가 소유한 Gem 목록을 최신순으로 조회합니다.

        Args:
            member_id (str): 조회를 요청한 사용자의 ID.

        Returns:
            list[GemEntity]: 정렬되어 조회된 Gem 엔티티 목록.
        """
        result = await self.orm_session.execute(
            select(GemEntity)
            .where(GemEntity.member_id == member_id)
            .order_by(GemEntity.created_at.desc())
        )
        return list(result.scalars().all())

    async def select_by_id(self, gem_id: str) -> GemEntity | None:
        """Gem ID로 단건 조회합니다.

        Args:
            gem_id (str): 조회 대상 Gem의 ID.

        Returns:
            GemEntity | None: 조회된 Gem 엔티티 또는 존재하지 않을 경우 None.
        """
        return await self.orm_session.get(GemEntity, gem_id)

    async def update(self, gem_entity: GemEntity) -> GemEntity:
        """Gem 메타데이터를 업데이트하고 최신 상태를 반환합니다.

        Args:
            gem_entity (GemEntity): 수정할 메타데이터가 담긴 Gem 엔티티.

        Returns:
            GemEntity: 업데이트 및 영속화가 완료된 Gem 엔티티.
        """
        self.logger.info(f"update 실행: gem_id={gem_entity.gem_id}")
        merged = await self.orm_session.merge(gem_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(merged)
        return merged

    async def delete(self, gem_id: str) -> None:
        """Gem을 ID 기준으로 삭제합니다.

        Args:
            gem_id (str): 삭제할 Gem의 ID.
        """
        gem = await self.select_by_id(gem_id)
        if gem:
            await self.orm_session.delete(gem)

    async def insert_file(self, gem_id: str, filename: str, chunk_count: int) -> GemFileEntity:
        """파일 메타데이터를 gem_file 테이블에 삽입합니다.

        Args:
            gem_id (str): 파일을 등록할 Gem의 ID.
            filename (str): 업로드된 원본 파일명.
            chunk_count (int): 추출 및 분할된 텍스트 청크 수.

        Returns:
            GemFileEntity: 저장된 파일 메타데이터 엔티티.
        """
        self.logger.info(f"insert_file 실행: gem_id={gem_id}, filename={filename}")
        entity = GemFileEntity(
            file_id=str(uuid.uuid4()),
            gem_id=gem_id,
            filename=filename,
            chunk_count=chunk_count,
        )
        self.orm_session.add(entity)
        await self.orm_session.flush()
        return entity

    async def select_files_by_gem_id(self, gem_id: str) -> list[GemFileEntity]:
        """특정 Gem에 업로드된 파일 목록을 업로드 시간 순으로 반환합니다.

        Args:
            gem_id (str): 조회 대상 Gem의 ID.

        Returns:
            list[GemFileEntity]: 업로드된 파일 목록.
        """
        self.logger.info(f"select_files_by_gem_id 실행: gem_id={gem_id}")
        result = await self.orm_session.execute(
            select(GemFileEntity)
            .where(GemFileEntity.gem_id == gem_id)
            .order_by(GemFileEntity.uploaded_at.asc())
        )
        return list(result.scalars().all())


GemDaoDep = Annotated[GemDao, Depends(GemDao)]

