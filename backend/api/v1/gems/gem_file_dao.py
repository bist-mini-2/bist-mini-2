import uuid
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select
from api.database.config.dbsession import OrmSessionDep
from api.v1.gems.gem_file_entity import GemFileEntity


class GemFileDao:
    """gem_file 테이블 데이터 접근 객체."""

    def __init__(self, session: OrmSessionDep) -> None:
        self.session = session

    async def insert(self, gem_id: str, filename: str, chunk_count: int) -> GemFileEntity:
        """파일 메타데이터를 gem_file 테이블에 삽입한다."""
        entity = GemFileEntity(
            file_id=str(uuid.uuid4()),
            gem_id=gem_id,
            filename=filename,
            chunk_count=chunk_count,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def select_by_gem_id(self, gem_id: str) -> list[GemFileEntity]:
        """특정 Gem에 업로드된 파일 목록을 업로드 시간 순으로 반환한다."""
        result = await self.session.execute(
            select(GemFileEntity)
            .where(GemFileEntity.gem_id == gem_id)
            .order_by(GemFileEntity.uploaded_at.asc())
        )
        return list(result.scalars().all())


GemFileDaoDep = Annotated[GemFileDao, Depends(GemFileDao)]
