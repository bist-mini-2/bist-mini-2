import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.common.auth import LoginCheckDep, AdminCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.member.entity import MemberEntity
from api.v1.member.services import MemberServiceDep
from api.v1.member.models import (
    MemberJoinRequest,
    MemberJoinResponse,
    MemberInfoResponse,
    MemberModifyRequest,
    MemberModifyResponse,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/member", tags=["회원 관리"])


@router.post("/join", response_class=JSONResponse, response_model=SuccessResponse, status_code=status.HTTP_201_CREATED, summary="신규 회원 가입 API")
async def join(
    member_join_request: MemberJoinRequest,
    member_service: MemberServiceDep
):
    """입력받은 회원 가입 정보(아이디, 패스워드, 이름, 이메일 등)를 검증하고 신규 회원 데이터를 적재합니다.

    Args:
        member_join_request (MemberJoinRequest): 가입할 회원의 신규 정보 요청 DTO.
        member_service (MemberServiceDep): 회원 관련 비즈니스 로직을 수행하는 서비스 의존성.

    Returns:
        SuccessResponse: 등록 완료된 회원의 식별자와 가입 처리 결과를 포함하는 성공 응답 객체.
    """
    member_entity = MemberEntity(**member_join_request.model_dump())
    member_entity = await member_service.join(member_entity)
    return SuccessResponse(
        data=MemberJoinResponse.model_validate(member_entity)
    )


@router.get("/info", response_class=JSONResponse, response_model=SuccessResponse, summary="회원 정보 조회 API")
async def info(payload: LoginCheckDep, member_service: MemberServiceDep) -> SuccessResponse:
    """JWT 토큰에서 추출한 mid 식별자에 해당하는 회원의 상세 프로필 정보를 조회합니다.

    Args:
        payload (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드.
        member_service (MemberServiceDep): 회원 프로필 조회를 수행하는 서비스 의존성.

    Returns:
        SuccessResponse: 조회 완료된 사용자의 프로필 정보(이름, 역할 등)를 포함하는 성공 응답 객체.
    """
    mid = payload["sub"]
    member_entity = await member_service.read(mid)
    return SuccessResponse(
        data=MemberInfoResponse.model_validate(member_entity)
    )


@router.put("/modify", response_class=JSONResponse, response_model=SuccessResponse, summary="회원 정보 수정 API")
async def update(
    payload: LoginCheckDep,
    member_modify_request: MemberModifyRequest,
    member_service: MemberServiceDep
):
    """현재 로그인 유저의 이름, 이메일 또는 비밀번호 등의 회원 정보를 안전하게 수정합니다.

    Args:
        payload (LoginCheckDep): 현재 로그인 사용자의 JWT 페이로드 정보.
        member_modify_request (MemberModifyRequest): 수정할 정보 항목이 담긴 요청 DTO.
        member_service (MemberServiceDep): 회원 정보 수정을 처리하는 서비스 의존성.

    Returns:
        SuccessResponse: 수정 완료된 회원의 반영 결과를 포함하는 성공 응답 객체.
    """
    member_entity = MemberEntity(**member_modify_request.model_dump(exclude_unset=True))
    member_entity.mid = payload["sub"]
    member_entity = await member_service.modify(member_entity)
    return SuccessResponse(
        data=MemberModifyResponse.model_validate(member_entity)
    )


@router.delete("/delete/{mid}", response_class=JSONResponse, response_model=SuccessResponse, summary="회원 강제 탈퇴(삭제) API")
async def delete(
    payload: AdminCheckDep,
    member_service: MemberServiceDep,
    mid: str
):
    """지정한 특정 회원 ID(mid)에 해당하는 회원을 플랫폼에서 강제 탈퇴시키고 데이터를 제거합니다. (관리자 전용)

    Args:
        payload (AdminCheckDep): 관리자 역할(ROLE_ADMIN) 권한 검증 정보.
        member_service (MemberServiceDep): 회원 강제 삭제를 처리하는 서비스 의존성.
        mid (str): 삭제(강제 탈퇴) 대상 회원의 고유 식별자 ID.

    Returns:
        SuccessResponse: 탈퇴 완료된 대상 회원 ID 정보를 포함하는 성공 응답 객체.
    """
    await member_service.delete(mid)
    return SuccessResponse(
        data={"message": f"삭제된 회원의 아이디: {mid}"}
    )
