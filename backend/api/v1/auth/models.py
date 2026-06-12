from api.database.config.dto_base import BaseDTO, SuccessResponse


class TokenResponse(BaseDTO):
    """로그인 성공 시 반환되는 액세스 토큰 정보 스키마입니다."""
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class TokenResponseWrapper(SuccessResponse):
    """토큰 응답 성공 공통 래퍼 스키마입니다."""
    data: TokenResponse


class UserInfoResponse(BaseDTO):
    """현재 로그인한 사용자의 정보를 반환하는 스키마입니다."""
    username: str
    role: str


class UserInfoResponseWrapper(SuccessResponse):
    """사용자 정보 성공 공통 래퍼 스키마입니다."""
    data: UserInfoResponse
