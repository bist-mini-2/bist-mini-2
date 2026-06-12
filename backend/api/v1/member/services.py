import logging
from typing import Annotated
from fastapi import Depends
import bcrypt
from api.v1.member.dao import MemberDaoDep
from api.v1.member.entity import MemberEntity
from api.common.exceptions import MemberNotFoundError, InvalidPasswordError

logger = logging.getLogger(__name__)


class MemberService:
    """회원가입, 로그인 및 개인 정보 조회/수정과 관련된 비즈니스 로직을 처리합니다."""

    def __init__(self, member_dao: MemberDaoDep) -> None:
        self.logger = logging.getLogger(f"{__name__}.MemberService")
        self.member_dao = member_dao

    async def join(self, member_entity: MemberEntity) -> MemberEntity:
        """비밀번호를 암호화하여 회원 정보를 영구 저장소에 추가합니다."""
        self.logger.info("join 실행")
        hashed = bcrypt.hashpw(member_entity.mpassword.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        member_entity.mpassword = hashed
        member_entity = await self.member_dao.insert(member_entity)
        return member_entity

    async def authenticate(self, mid: str, password: str) -> MemberEntity:
        """아이디와 비밀번호를 검증하여 일치할 경우 MemberEntity를 반환합니다.

        Args:
            mid (str): 회원 아이디
            password (str): 회원 비밀번호

        Returns:
            MemberEntity: 검증에 성공한 회원 엔티티 정보

        Raises:
            MemberNotFoundError: 회원이 존재하지 않는 경우
            InvalidPasswordError: 비밀번호가 일치하지 않는 경우
        """
        self.logger.info("authenticate 실행")
        db_member_entity = await self.member_dao.select_by_mid(mid)
        if not db_member_entity:
            raise MemberNotFoundError("존재하지 않는 회원 아이디")
        if not bcrypt.checkpw(password.encode('utf-8'), db_member_entity.mpassword.encode('utf-8')):
            raise InvalidPasswordError("회원 비밀번호가 틀림")
        return db_member_entity

    async def read(self, mid: str) -> MemberEntity | None:
        """특정 회원 정보를 ID 기준으로 읽어옵니다."""
        return await self.member_dao.select_by_mid(mid)

    async def modify(self, member_entity: MemberEntity) -> MemberEntity:
        """회원 비밀번호 등을 업데이트하며, 비밀번호 변경 시 다시 암호화 해싱을 수행합니다."""
        if member_entity.mpassword:
            hashed = bcrypt.hashpw(member_entity.mpassword.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            member_entity.mpassword = hashed
        return await self.member_dao.update(member_entity)

    async def delete(self, mid: str):
        """특정 사용자를 계정 정보에서 완전히 삭제합니다."""
        await self.member_dao.delete(mid)


MemberServiceDep = Annotated[MemberService, Depends(MemberService)]
