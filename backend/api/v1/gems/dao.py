import logging
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from api.database.config.dbsession import OrmSessionDep
from api.v1.gems.entity import GemEntity


class GemDao:
    """gem 테이블에 대한 ORM 작업을 수행하는 데이터 액세스 객체(DAO)입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        self.logger = logging.getLogger(f"{__name__}.GemDao")
        self.orm_session = orm_session

    async def insert(self, gem_entity: GemEntity) -> GemEntity:
        """새로운 Gem을 저장합니다."""
        self.logger.info("insert 실행")
        self.orm_session.add(gem_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(gem_entity)
        return gem_entity

    async def select_by_member(self, member_id: str) -> list[GemEntity]:
        """특정 사용자가 소유한 Gem 목록을 최신순으로 조회합니다."""
        result = await self.orm_session.execute(
            select(GemEntity)
            .where(GemEntity.member_id == member_id)
            .order_by(GemEntity.created_at.desc())
        )
        return list(result.scalars().all())

    async def select_by_id(self, gem_id: str) -> GemEntity | None:
        """Gem ID로 단건 조회합니다."""
        return await self.orm_session.get(GemEntity, gem_id)

    async def update(self, gem_entity: GemEntity) -> GemEntity:
        """Gem 메타데이터를 업데이트하고 최신 상태를 반환합니다."""
        self.logger.info(f"update 실행: gem_id={gem_entity.gem_id}")
        merged = await self.orm_session.merge(gem_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(merged)
        return merged

    async def delete(self, gem_id: str) -> None:
        """Gem을 ID 기준으로 삭제합니다."""
        gem = await self.select_by_id(gem_id)
        if gem:
            await self.orm_session.delete(gem)


GemDaoDep = Annotated[GemDao, Depends(GemDao)]
