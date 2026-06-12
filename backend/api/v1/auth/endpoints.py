from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.common.auth import LoginCheckDep, AdminCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.auth.services import AuthServiceDep
from api.v1.auth.models import (
    TokenResponse,
    UserInfoResponse,
    UserInfoResponseWrapper,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep
):
    """OAuth2 호환 토큰 로그인 엔드포인트입니다."""
    login_result = await auth_service.login(form_data.username, form_data.password)
    return TokenResponse(**login_result)


@router.get("/me", response_model=UserInfoResponseWrapper)
async def get_me(payload: LoginCheckDep):
    """인증된 현재 사용자의 정보를 조회합니다."""
    return UserInfoResponseWrapper(
        data=UserInfoResponse(
            username=payload["sub"],
            role=payload["mrole"]
        )
    )


@router.get("/admin-only", response_model=SuccessResponse)
async def admin_only(payload: AdminCheckDep):
    """관리자 권한을 가진 사용자만 접근 가능한 보호된 리소스를 조회합니다."""
    return SuccessResponse(
        data={
            "message": f"Hello Admin '{payload['sub']}'! You have successfully accessed this protected endpoint."
        }
    )
