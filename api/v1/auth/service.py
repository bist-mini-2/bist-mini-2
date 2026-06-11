from fastapi import HTTPException, status
from typing import Annotated
from fastapi import Depends
import logging
from passlib.context import CryptContext

from api.common.auth import create_token
from api.v1.auth.dao import MemberDaoDep
from api.v1.auth.entities import MemberEntity
from api.v1.auth.schemas import MemberJoinRequest

logger = logging.getLogger(__name__)


class AuthService:
    """인증 비즈니스 로직을 처리하는 서비스 레이어 클래스입니다."""

    def __init__(self, member_dao: MemberDaoDep):
        """AuthService의 생성자입니다.

        Args:
            member_dao (MemberDao): 의존성 주입을 통해 전달받은 회원 DAO 인스턴스.
        """
        self.member_dao = member_dao
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def join(self, join_req: MemberJoinRequest) -> MemberEntity:
        """신규 회원 등록(회원가입) 비즈니스 로직을 처리합니다.

        아이디와 이메일 중복 검사를 수행한 후, 비밀번호를 bcrypt 방식으로 암호화하여 DB에 저장합니다.

        Args:
            join_req (MemberJoinRequest): 회원가입 요청 DTO 객체.

        Returns:
            MemberEntity: 데이터베이스에 성공적으로 저장된 회원 엔티티 객체.

        Raises:
            HTTPException: 이미 등록된 ID나 이메일인 경우 400 Bad Request 예외를 발생시킵니다.
        """
        # 아이디 중복 체크
        existing_id = await self.member_dao.select_by_mid(join_req.mid)
        if existing_id:
            logger.warning(f"Registration failed: ID '{join_req.mid}' is already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 회원 아이디입니다."
            )

        # 이메일 중복 체크
        existing_email = await self.member_dao.select_by_memail(join_req.memail)
        if existing_email:
            logger.warning(f"Registration failed: Email '{join_req.memail}' is already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일 주소입니다."
            )

        # 비밀번호 암호화
        hashed_password = self.pwd_context.hash(join_req.mpassword)

        # 엔티티 생성 및 데이터베이스 삽입
        new_member = MemberEntity(
            mid=join_req.mid,
            mname=join_req.mname,
            mpassword=hashed_password,
            memail=join_req.memail,
            menabled=True,
            mrole="ROLE_USER"  # 회원가입 시 기본 사용자 권한 부여
        )

        member_entity = await self.member_dao.insert(new_member)
        logger.info(f"Successfully registered user: {member_entity.mid}")
        return member_entity

    async def authenticate(self, username: str, password: str) -> str:
        """사용자 이름과 비밀번호를 검증하여 적절한 권한(역할)을 반환합니다.

        Args:
            username (str): 검증할 사용자 이름(아이디).
            password (str): 검증할 비밀번호.

        Returns:
            str: 검증에 성공한 사용자의 권한 역할 명칭 (예: ROLE_ADMIN, ROLE_USER).

        Raises:
            HTTPException: 자격 증명이 유효하지 않거나 계정이 비활성화 상태인 경우 HTTP 예외를 발생시킵니다.
        """
        # 데이터베이스에서 사용자 조회
        member = await self.member_dao.select_by_mid(username)
        if not member:
            logger.warning(f"Failed login attempt: User '{username}' not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 비밀번호 검증
        if not self.pwd_context.verify(password, member.mpassword):
            logger.warning(f"Failed login attempt: Incorrect password for user '{username}'.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 활성화 여부 확인
        if not member.menabled:
            logger.warning(f"Login attempt failed: User '{username}' account is disabled.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 계정은 비활성화 상태입니다. 관리자에게 문의하세요."
            )

        return member.mrole

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

    async def get_user_info(self, username: str) -> dict:
        """아이디(username)를 바탕으로 데이터베이스에서 사용자 정보를 조회합니다.

        Args:
            username (str): 조회할 사용자의 아이디.

        Returns:
            dict: 조회된 사용자의 이름 및 권한 역할 정보가 담긴 딕셔너리.

        Raises:
            HTTPException: 사용자가 데이터베이스에 존재하지 않는 경우 404 Not Found 예외를 발생시킵니다.
        """
        member = await self.member_dao.select_by_mid(username)
        if not member:
            logger.warning(f"User info retrieval failed: User '{username}' not found in database.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 회원 정보입니다."
            )

        return {
            "username": member.mid,
            "role": member.mrole
        }


# Dependency injection alias for the service
AuthServiceDep = Annotated[AuthService, Depends(AuthService)]
