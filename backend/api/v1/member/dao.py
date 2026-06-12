import logging
from typing import Annotated
from fastapi import Depends
from sqlalchemy import text
from api.database.config.dbsession import OrmSessionDep
from api.v1.member.entity import MemberEntity
from api.common.exceptions import BusinessException


class MemberDao:
    """Member 테이블에 직접 SQL 쿼리 및 ORM 작업을 수행하는 데이터 액세스 객체(DAO)입니다."""

    def __init__(self, orm_session: OrmSessionDep):
        self.logger = logging.getLogger(f"{__name__}.MemberDao")
        self.orm_session = orm_session

    async def insert(self, member_entity: MemberEntity) -> MemberEntity:
        """새로운 회원 정보를 데이터베이스에 저장합니다."""
        self.logger.info("insert 실행")
        self.orm_session.add(member_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(member_entity)
        return member_entity

    async def update(self, member_entity: MemberEntity) -> MemberEntity:
        """기존 회원 정보를 수정합니다."""
        db_member_entity = await self.orm_session.get(MemberEntity, member_entity.mid)
        if not db_member_entity:
            raise BusinessException(f"존재하지 않는 회원 아이디: {member_entity.mid}")

        if member_entity.mpassword:
            db_member_entity.mpassword = member_entity.mpassword
        if member_entity.menabled is not None:
            db_member_entity.menabled = member_entity.menabled
        if member_entity.memail:
            db_member_entity.memail = member_entity.memail

        await self.orm_session.flush()
        await self.orm_session.refresh(db_member_entity)
        return db_member_entity

    async def delete(self, mid: str):
        """특정 사용자를 ID 기준으로 삭제합니다."""
        await self.orm_session.execute(
            text("DELETE FROM member WHERE mid = :mid"),
            {"mid": mid}
        )

    async def select_by_mid(self, mid: str) -> MemberEntity | None:
        """회원 ID로 회원 상세 정보를 조회합니다."""
        member_entity = await self.orm_session.get(MemberEntity, mid)
        return member_entity


MemberDaoDep = Annotated[MemberDao, Depends(MemberDao)]
