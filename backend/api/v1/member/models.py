from typing import Annotated
from pydantic import Field, EmailStr
from api.database.config.dto_base import BaseDTO, SuccessResponse


class MemberJoinRequest(BaseDTO):
    """회원 가입 요청 데이터 모델 스키마입니다."""
    mid: Annotated[str, Field(min_length=5, max_length=20)]
    mname: Annotated[str, Field(min_length=2, max_length=20)]
    mpassword: Annotated[str, Field(min_length=5, max_length=20)]
    menabled: Annotated[bool, Field(default=True)]
    mrole: Annotated[str, Field(pattern="^(ROLE_USER|ROLE_ADMIN)$")] = "ROLE_USER"
    memail: EmailStr


class MemberJoinResponse(BaseDTO):
    """회원 가입 성공 후 반환되는 응답 스키마입니다."""
    mid: str
    mname: str
    mpassword: str | None = None
    menabled: bool
    mrole: str
    memail: str


class MemberJoinResponseWrapper(SuccessResponse):
    """회원 가입 성공 공통 래퍼 스키마입니다."""
    data: MemberJoinResponse


class MemberInfoResponse(BaseDTO):
    """특정 회원의 상세 정보 응답 스키마입니다."""
    mid: str
    mname: str
    mpassword: str
    menabled: bool
    mrole: str
    memail: EmailStr


class MemberInfoResponseWrapper(SuccessResponse):
    """회원 정보 조회 성공 공통 래퍼 스키마입니다."""
    data: MemberInfoResponse


class MemberModifyRequest(BaseDTO):
    """회원 정보 수정 요청 데이터 모델 스키마입니다."""
    mpassword: Annotated[str | None, Field(min_length=5, max_length=20)] = None
    menabled: bool | None = None
    memail: EmailStr | None = None


class MemberModifyResponse(BaseDTO):
    """회원 정보 수정 성공 후 반환되는 응답 스키마입니다."""
    mid: str
    mname: str
    mpassword: str | None = None
    menabled: bool
    mrole: str
    memail: str


class MemberModifyResponseWrapper(SuccessResponse):
    """회원 정보 수정 성공 공통 래퍼 스키마입니다."""
    data: MemberModifyResponse
