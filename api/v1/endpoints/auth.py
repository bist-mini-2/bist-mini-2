from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.common.auth import LoginCheckDep, AdminCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.services.auth_service import AuthServiceDep
from api.v1.schemas.auth import (
    TokenResponse,
    TokenResponseWrapper,
    UserInfoResponse,
    UserInfoResponseWrapper,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponseWrapper)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep
):
    """OAuth2 호환 토큰 로그인 엔드포인트입니다.

    - **Admin**: username `admin` / password `admin`
    - **User**: username `user` / password `password`

    Args:
        form_data (OAuth2PasswordRequestForm): 사용자가 입력한 사용자명과 비밀번호 폼 데이터.
        auth_service (AuthService): 인증 처리를 위한 서비스 인스턴스.

    Returns:
        TokenResponseWrapper: 성공 상태값 및 발급된 액세스 토큰 정보.
    """
    login_result = await auth_service.login(form_data.username, form_data.password)

    return TokenResponseWrapper(data=TokenResponse(**login_result))


@router.get("/me", response_model=UserInfoResponseWrapper)
async def get_me(payload: LoginCheckDep):
    """인증된 현재 사용자의 정보를 조회합니다.

    Args:
        payload (dict): JWT 토큰 디코딩을 통해 획득한 로그인 페이로드 정보.

    Returns:
        UserInfoResponseWrapper: 성공 상태값 및 현재 로그인한 사용자의 이름 및 권한 정보.
    """
    return UserInfoResponseWrapper(
        data=UserInfoResponse(
            username=payload["sub"],
            role=payload["mrole"]
        )
    )


@router.get("/admin-only", response_model=SuccessResponse)
async def admin_only(payload: AdminCheckDep):
    """관리자 권한을 가진 사용자만 접근 가능한 보호된 리소스를 조회합니다.

    Args:
        payload (dict): JWT 토큰 디코딩을 통해 획득한 관리자 권한 페이로드 정보.

    Returns:
        SuccessResponse: 성공 상태값 및 환영 메시지가 포함된 딕셔너리 객체.
    """
    return SuccessResponse(
        data={
            "message": f"Hello Admin '{payload['sub']}'! You have successfully accessed this protected endpoint."
        }
    )


