from typing import Annotated
from pydantic import Field, EmailStr
from api.database.config.dto_base import BaseDTO


class MemberJoinRequest(BaseDTO):
    """회원 가입 요청 데이터 모델 스키마입니다."""
    mid: Annotated[str, Field(
        min_length=5,
        max_length=20,
        description="회원 ID",
        examples=["testuser"]
    )]
    mname: Annotated[str, Field(
        min_length=2,
        max_length=20,
        description="회원 이름",
        examples=["홍길동"]
    )]
    mpassword: Annotated[str, Field(
        min_length=5,
        max_length=20,
        description="비밀번호",
        examples=["password123"]
    )]
    menabled: Annotated[bool, Field(
        default=True,
        description="계정 활성화 여부",
        examples=[True]
    )]
    mrole: Annotated[str, Field(
        pattern="^(ROLE_USER|ROLE_ADMIN)$",
        description="사용자 권한 (ROLE_USER 또는 ROLE_ADMIN)",
        examples=["ROLE_USER"]
    )] = "ROLE_USER"
    memail: EmailStr = Field(
        ...,
        description="이메일 주소",
        examples=["testuser@example.com"]
    )


class MemberJoinResponse(BaseDTO):
    """회원 가입 성공 후 반환되는 응답 스키마입니다."""
    mid: str = Field(..., description="회원 ID", examples=["testuser"])
    mname: str = Field(..., description="회원 이름", examples=["홍길동"])
    mpassword: str | None = Field(None, description="비밀번호 (보안상 비공개)", examples=[None])
    menabled: bool = Field(..., description="계정 활성화 여부", examples=[True])
    mrole: str = Field(..., description="사용자 권한", examples=["ROLE_USER"])
    memail: str = Field(..., description="이메일 주소", examples=["testuser@example.com"])


class MemberInfoResponse(BaseDTO):
    """특정 회원의 상세 정보 응답 스키마입니다."""
    mid: str = Field(..., description="회원 ID", examples=["testuser"])
    mname: str = Field(..., description="회원 이름", examples=["홍길동"])
    mpassword: str = Field(..., description="비밀번호 해시 값", examples=["$2b$12$EixZaYVK1u..."])
    menabled: bool = Field(..., description="계정 활성화 여부", examples=[True])
    mrole: str = Field(..., description="사용자 권한", examples=["ROLE_USER"])
    memail: EmailStr = Field(..., description="이메일 주소", examples=["testuser@example.com"])


class MemberModifyRequest(BaseDTO):
    """회원 정보 수정 요청 데이터 모델 스키마입니다."""
    mpassword: Annotated[str | None, Field(
        min_length=5,
        max_length=20,
        description="변경할 비밀번호 (선택)",
        examples=["newpassword123"]
    )] = None
    menabled: bool | None = Field(
        None,
        description="계정 활성화 여부 변경 (선택)",
        examples=[True]
    )
    memail: EmailStr | None = Field(
        None,
        description="변경할 이메일 주소 (선택)",
        examples=["newemail@example.com"]
    )


class MemberModifyResponse(BaseDTO):
    """회원 정보 수정 성공 후 반환되는 응답 스키마입니다."""
    mid: str = Field(..., description="회원 ID", examples=["testuser"])
    mname: str = Field(..., description="회원 이름", examples=["홍길동"])
    mpassword: str | None = Field(None, description="비밀번호 (보안상 비공개)", examples=[None])
    menabled: bool = Field(..., description="계정 활성화 여부", examples=[True])
    mrole: str = Field(..., description="사용자 권한", examples=["ROLE_USER"])
    memail: str = Field(..., description="이메일 주소", examples=["newemail@example.com"])
