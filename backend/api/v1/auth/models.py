from pydantic import Field
from api.database.config.dto_base import BaseDTO


class TokenResponse(BaseDTO):
    """로그인 성공 시 반환되는 액세스 토큰 정보 스키마입니다."""
    access_token: str = Field(
        ...,
        description="JWT 액세스 토큰",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        "bearer",
        description="토큰 타입",
        examples=["bearer"]
    )
    username: str = Field(
        ...,
        description="사용자 ID",
        examples=["testuser"]
    )
    role: str = Field(
        ...,
        description="사용자 권한",
        examples=["ROLE_USER"]
    )


class UserInfoResponse(BaseDTO):
    """현재 로그인한 사용자의 정보를 반환하는 스키마입니다."""
    username: str = Field(
        ...,
        description="사용자 ID",
        examples=["testuser"]
    )
    role: str = Field(
        ...,
        description="사용자 권한",
        examples=["ROLE_USER"]
    )
