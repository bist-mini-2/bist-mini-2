from fastapi import HTTPException, status
from typing import Annotated
from fastapi import Depends
import logging

from api.common.auth import create_token

logger = logging.getLogger(__name__)


class AuthService:
    """인증 비즈니스 로직을 처리하는 서비스 레이어 클래스입니다."""

    async def authenticate(self, username: str, password: str) -> str:
        """사용자 이름과 비밀번호를 검증하여 적절한 권한(역할)을 반환합니다.

        Args:
            username (str): 검증할 사용자 이름.
            password (str): 검증할 비밀번호.

        Returns:
            str: 검증에 성공한 사용자의 권한 역할 명칭 (예: ROLE_ADMIN, ROLE_USER).

        Raises:
            HTTPException: 자격 증명이 유효하지 않을 때 401 Unauthorized 예외를 발생시킵니다.
        """
        if username == "admin" and password == "admin":
            return "ROLE_ADMIN"
        elif username == "user" and password == "password":
            return "ROLE_USER"
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def login(self, username: str, password: str) -> dict:
        """사용자를 인증하고 JWT 액세스 토큰을 생성하여 반환합니다.

        Args:
            username (str): 로그인할 사용자 이름.
            password (str): 로그인할 비밀번호.

        Returns:
            dict: 액세스 토큰, 토큰 타입, 사용자 이름 및 역할 권한을 포함하는 딕셔너리 객체.

        Raises:
            HTTPException: 자격 증명이 유효하지 않을 때 예외를 발생시킵니다.
        """
        role = await self.authenticate(username, password)
        access_token = create_token(username, role)
        logger.info(f"Successful login for {username} with role {role}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": username,
            "role": role
        }


# Dependency injection alias for the service
AuthServiceDep = Annotated[AuthService, Depends(AuthService)]
