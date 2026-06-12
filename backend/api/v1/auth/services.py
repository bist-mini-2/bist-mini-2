from fastapi import Depends
from typing import Annotated
import logging

from api.common.auth import create_token
from api.v1.member.services import MemberServiceDep

logger = logging.getLogger(__name__)


class AuthService:
    """인증 비즈니스 로직을 처리하는 서비스 레이어 클래스입니다."""

    def __init__(self, member_service: MemberServiceDep) -> None:
        """AuthService의 인스턴스를 초기화하고 MemberService 의존성을 주입합니다.

        Args:
            member_service (MemberService): 회원 정보를 관리하는 서비스 레이어 인스턴스.
        """
        self.member_service = member_service

    async def login(self, username: str, password: str) -> dict:
        """사용자를 인증하고 JWT 액세스 토큰을 생성하여 반환합니다.

        Args:
            username (str): 사용자 아이디 (mid)
            password (str): 사용자 비밀번호 (mpassword)

        Returns:
            dict: 토큰 정보(access_token, token_type, username, role)를 담은 딕셔너리
        """
        member_entity = await self.member_service.authenticate(username, password)
        access_token = create_token(member_entity.mid, member_entity.mrole)
        logger.info(f"Successful login for {member_entity.mid} with role {member_entity.mrole}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": member_entity.mid,
            "role": member_entity.mrole
        }


AuthServiceDep = Annotated[AuthService, Depends(AuthService)]
