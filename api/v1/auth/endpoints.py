from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from api.common.auth import LoginCheckDep, AdminCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.auth.service import AuthServiceDep
from api.v1.auth.schemas import (
    TokenResponse,
    TokenResponseWrapper,
    UserInfoResponse,
    UserInfoResponseWrapper,
    MemberJoinRequest,
    MemberJoinResponse,
    MemberJoinResponseWrapper,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/join", response_model=MemberJoinResponseWrapper)
async def join(
    join_req: MemberJoinRequest,
    auth_service: AuthServiceDep
):
    """신규 회원가입을 위한 엔드포인트입니다.

    아이디와 이메일 중복 체크를 거쳐 데이터베이스에 회원을 등록합니다.

    Args:
        join_req (MemberJoinRequest): 가입할 회원 정보 (아이디, 이름, 비밀번호, 이메일).
        auth_service (AuthService): 회원가입 비즈니스 로직을 제공하는 서비스 인스턴스.

    Returns:
        MemberJoinResponseWrapper: 성공 상태값 및 가입 완료된 회원 정보.
    """
    member_entity = await auth_service.join(join_req)
    return MemberJoinResponseWrapper(
        data=MemberJoinResponse.model_validate(member_entity)
    )


@router.post("/login", response_model=TokenResponseWrapper)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep
):
    """OAuth2 호환 토큰 로그인 엔드포인트입니다.

    데이터베이스 정보를 기반으로 사용자를 인증하고 액세스 토큰을 반환합니다.

    Args:
        form_data (OAuth2PasswordRequestForm): 사용자가 입력한 사용자명과 비밀번호 폼 데이터.
        auth_service (AuthService): 인증 처리를 위한 서비스 인스턴스.

    Returns:
        TokenResponseWrapper: 성공 상태값 및 발급된 액세스 토큰 정보.
    """
    login_result = await auth_service.login(form_data.username, form_data.password)

    return TokenResponseWrapper(data=TokenResponse(**login_result))


@router.get("/me", response_model=UserInfoResponseWrapper)
async def get_me(
    payload: LoginCheckDep,
    auth_service: AuthServiceDep
):
    """인증된 현재 사용자의 정보를 조회합니다.

    Args:
        payload (dict): JWT 토큰 디코딩을 통해 획득한 로그인 페이로드 정보.
        auth_service (AuthService): 회원 정보 로드를 위한 서비스 인스턴스.

    Returns:
        UserInfoResponseWrapper: 성공 상태값 및 현재 로그인한 사용자의 이름 및 권한 정보.
    """
    user_info = await auth_service.get_user_info(payload["sub"])
    return UserInfoResponseWrapper(
        data=UserInfoResponse(
            username=user_info["username"],
            role=user_info["role"]
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
