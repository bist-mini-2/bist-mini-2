from typing import Annotated
import logging
from fastapi import Depends
from sqlalchemy import select, delete

from api.database.config.dbsession import OrmSessionDep
from api.v1.auth.entities import MemberEntity

logger = logging.getLogger(__name__)


class MemberDao:
    """회원(Member) 데이터베이스 접근을 담당하는 DAO(Data Access Object) 클래스입니다.

    SQLAlchemy 비동기 세션을 주입받아 데이터베이스 CRUD 작업을 수행합니다.
    """

    def __init__(self, orm_session: OrmSessionDep):
        """MemberDao의 생성자입니다.

        Args:
            orm_session (AsyncSession): 의존성 주입을 통해 전달받은 비동기 데이터베이스 세션.
        """
        self.orm_session = orm_session

    async def insert(self, member_entity: MemberEntity) -> MemberEntity:
        """새로운 회원 정보를 데이터베이스에 삽입합니다.

        Args:
            member_entity (MemberEntity): 가입 요청으로 생성된 회원 ORM 엔티티 객체.

        Returns:
            MemberEntity: 데이터베이스에 삽입되고 식별자 등이 동기화된 회원 ORM 엔티티 객체.
        """
        self.orm_session.add(member_entity)
        await self.orm_session.flush()
        await self.orm_session.refresh(member_entity)
        return member_entity

    async def select_by_mid(self, mid: str) -> MemberEntity | None:
        """회원 ID(mid)를 기준으로 회원을 조회합니다.

        Args:
            mid (str): 조회할 회원의 고유 ID.

        Returns:
            MemberEntity | None: 조회된 회원 엔티티 객체. 존재하지 않을 경우 None을 반환합니다.
        """
        return await self.orm_session.get(MemberEntity, mid)

    async def select_by_memail(self, memail: str) -> MemberEntity | None:
        """이메일 주소(memail)를 기준으로 회원을 조회합니다.

        Args:
            memail (str): 조회할 회원의 이메일 주소.

        Returns:
            MemberEntity | None: 조회된 회원 엔티티 객체. 존재하지 않을 경우 None을 반환합니다.
        """
        stmt = select(MemberEntity).where(MemberEntity.memail == memail)
        result = await self.orm_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, member_entity: MemberEntity) -> MemberEntity:
        """회원 정보를 데이터베이스에 갱신합니다.

        Args:
            member_entity (MemberEntity): 수정할 변경 사항이 반영된 회원 ORM 엔티티 객체.

        Returns:
            MemberEntity: 수정 및 동기화가 완료된 회원 ORM 엔티티 객체.
        """
        db_member_entity = await self.select_by_mid(member_entity.mid)
        if not db_member_entity:
            raise ValueError(f"존재하지 않는 회원 아이디: {member_entity.mid}")

        # 필드별 데이터 업데이트 수행
        if member_entity.mname:
            db_member_entity.mname = member_entity.mname
        if member_entity.mpassword:
            db_member_entity.mpassword = member_entity.mpassword
        if member_entity.memail:
            db_member_entity.memail = member_entity.memail
        if member_entity.menabled is not None:
            db_member_entity.menabled = member_entity.menabled
        if member_entity.mrole:
            db_member_entity.mrole = member_entity.mrole

        await self.orm_session.flush()
        await self.orm_session.refresh(db_member_entity)
        return db_member_entity

    async def delete(self, mid: str) -> None:
        """회원 ID(mid)를 기준으로 회원을 삭제합니다.

        Args:
            mid (str): 삭제할 회원의 고유 ID.
        """
        stmt = delete(MemberEntity).where(MemberEntity.mid == mid)
        await self.orm_session.execute(stmt)
        await self.orm_session.flush()


# 의존성 주입을 위한 타입 별칭 정의
MemberDaoDep = Annotated[MemberDao, Depends(MemberDao)]
