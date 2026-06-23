from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.common.auth import LoginCheckDep, AdminCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.auth.services import AuthServiceDep
from api.v1.auth.models import TokenResponse, UserInfoResponse

router = APIRouter(prefix="/auth", tags=["사용자 인증"])


@router.post("/login", response_model=TokenResponse, summary="OAuth2 로그인 및 토큰 발급 API")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep
):
    """사용자 자격 증명을 검증하여 OAuth2 규격에 부합하는 액세스 토큰을 발급합니다.

    Args:
        form_data (OAuth2PasswordRequestForm): 로그인 사용자 ID(username) 및 비밀번호(mpassword).
        auth_service (AuthServiceDep): 회원 인증 관련 처리를 담당하는 비즈니스 레이어 서비스.

    Returns:
        TokenResponse: 발급된 액세스 토큰과 토큰 타입 정보를 포함하는 DTO 객체.
    """
    login_result = await auth_service.login(form_data.username, form_data.password)
    return TokenResponse(**login_result)


@router.get("/me", response_model=SuccessResponse, summary="현재 로그인 사용자 정보 조회 API")
async def get_me(payload: LoginCheckDep):
    """인증 정보(JWT 토큰)를 기반으로 현재 로그인한 사용자의 계정 ID 및 권한 역할을 반환합니다.

    Args:
        payload (LoginCheckDep): 인증 검증 및 복호화가 완료된 현재 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 현재 사용자의 사용자명(username) 및 역할을 담은 성공 응답 객체.
    """
    return SuccessResponse(
        data=UserInfoResponse(
            username=payload["sub"],
            role=payload["mrole"]
        )
    )


@router.get("/admin-only", response_model=SuccessResponse, summary="관리자 전용 리소스 조회 API")
async def admin_only(payload: AdminCheckDep):
    """관리자 권한(ROLE_ADMIN)을 지닌 인증된 사용자만 접근할 수 있는 전용 테스트 리소스를 반환합니다.

    Args:
        payload (AdminCheckDep): 관리자 역할 권한 검사 및 토큰 검증이 완료된 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 관리자 전용 환영 메시지를 담은 성공 응답 객체.
    """
    return SuccessResponse(
        data={
            "message": f"Hello Admin '{payload['sub']}'! You have successfully accessed this protected endpoint."
        }
    )
