"""회원 서비스 및 인증 비즈니스 로직을 처리하는 모듈입니다."""

import logging
import asyncio
from typing import Annotated
from fastapi import Depends
import bcrypt
from api.v1.member.dao import MemberDaoDep
from api.v1.member.entity import MemberEntity
from api.common.exceptions import MemberNotFoundError, InvalidPasswordError, BusinessException

logger = logging.getLogger(__name__)


class MemberService:
    """회원가입, 로그인 및 개인 정보 조회/수정과 관련된 비즈니스 로직을 처리합니다."""

    def __init__(self, member_dao: MemberDaoDep) -> None:
        """MemberService 인스턴스를 초기화하고 MemberDao 의존성을 주입합니다.

        Args:
            member_dao (MemberDaoDep): 데이터베이스에 대한 데이터 액세스 객체.
        """
        self.logger = logging.getLogger(f"{__name__}.MemberService")
        self.member_dao = member_dao

    async def join(self, member_entity: MemberEntity) -> MemberEntity:
        """비밀번호를 암호화하여 회원 정보를 영구 저장소에 추가합니다.

        Args:
            member_entity (MemberEntity): 가입할 새로운 회원 정보 엔티티.

        Returns:
            MemberEntity: 암호화된 비밀번호가 적용되어 저장된 회원 정보 엔티티.

        Raises:
            BusinessException: 이미 존재하는 회원 ID일 경우
        """
        self.logger.info("join 실행")
        
        # 중복 아이디 존재 확인 및 400 Bad Request용 비즈니스 예외 처리
        existing = await self.member_dao.select_by_mid(member_entity.mid)
        if existing:
            raise BusinessException("이미 존재하는 회원 아이디입니다.", error_code="MEMBER_DUPLICATE")

        hashed = await asyncio.to_thread(
            bcrypt.hashpw,
            member_entity.mpassword.encode('utf-8'),
            bcrypt.gensalt()
        )
        member_entity.mpassword = hashed.decode('utf-8')
        member_entity = await self.member_dao.insert(member_entity)
        return member_entity

    async def authenticate(self, mid: str, password: str) -> MemberEntity:
        """아이디와 비밀번호를 검증하여 일치할 경우 MemberEntity를 반환합니다.

        Args:
            mid (str): 회원 아이디.
            password (str): 회원 비밀번호.

        Returns:
            MemberEntity: 검증에 성공한 회원 엔티티 정보.

        Raises:
            MemberNotFoundError: 회원이 존재하지 않는 경우
            InvalidPasswordError: 비밀번호가 일치하지 않는 경우
        """
        self.logger.info("authenticate 실행")
        db_member_entity = await self.member_dao.select_by_mid(mid)
        if not db_member_entity:
            raise MemberNotFoundError("존재하지 않는 회원 아이디")
        is_valid = await asyncio.to_thread(
            bcrypt.checkpw,
            password.encode('utf-8'),
            db_member_entity.mpassword.encode('utf-8')
        )
        if not is_valid:
            raise InvalidPasswordError("회원 비밀번호가 틀림")
        return db_member_entity

    async def read(self, mid: str) -> MemberEntity | None:
        """특정 회원 정보를 ID 기준으로 읽어옵니다.

        Args:
            mid (str): 조회하고자 하는 회원 아이디.

        Returns:
            MemberEntity | None: 회원 정보 엔티티 또는 존재하지 않는 경우 None.
        """
        return await self.member_dao.select_by_mid(mid)

    async def modify(self, member_entity: MemberEntity) -> MemberEntity:
        """회원 비밀번호 등을 업데이트하며, 비밀번호 변경 시 다시 암호화 해싱을 수행합니다.

        Args:
            member_entity (MemberEntity): 수정할 정보가 담긴 회원 엔티티.

        Returns:
            MemberEntity: 업데이트 완료 및 해싱된 비밀번호가 적용된 회원 엔티티 정보.
        """
        if member_entity.mpassword:
            hashed = await asyncio.to_thread(
                bcrypt.hashpw,
                member_entity.mpassword.encode('utf-8'),
                bcrypt.gensalt()
            )
            member_entity.mpassword = hashed.decode('utf-8')
        return await self.member_dao.update(member_entity)

    async def delete(self, mid: str):
        """특정 사용자를 계정 정보에서 완전히 삭제합니다.

        Args:
            mid (str): 삭제하고자 하는 회원 아이디.
        """
        await self.member_dao.delete(mid)


MemberServiceDep = Annotated[MemberService, Depends(MemberService)]
