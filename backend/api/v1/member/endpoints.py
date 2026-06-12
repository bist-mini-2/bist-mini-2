import logging
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from api.common.auth import LoginCheckDep, AdminCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.member.entity import MemberEntity
from api.v1.member.services import MemberServiceDep
from api.v1.member.models import (
    MemberJoinRequest,
    MemberJoinResponse,
    MemberJoinResponseWrapper,
    MemberInfoResponse,
    MemberInfoResponseWrapper,
    MemberModifyRequest,
    MemberModifyResponse,
    MemberModifyResponseWrapper,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/member", tags=["Member"])


@router.post("/join", response_class=JSONResponse, response_model=MemberJoinResponseWrapper)
async def join(
    member_join_request: MemberJoinRequest,
    member_service: MemberServiceDep
):
    """새로운 회원을 가입 시키는 엔드포인트입니다."""
    member_entity = MemberEntity(**member_join_request.model_dump())
    member_entity = await member_service.join(member_entity)
    return MemberJoinResponseWrapper(
        data=MemberJoinResponse.model_validate(member_entity)
    )



@router.get("/info", response_class=JSONResponse, response_model=MemberInfoResponseWrapper)
async def info(payload: LoginCheckDep, member_service: MemberServiceDep) -> MemberInfoResponseWrapper:
    """인증된 현재 로그인 유저의 정보를 조회합니다."""
    mid = payload["sub"]
    member_entity = await member_service.read(mid)
    return MemberInfoResponseWrapper(
        data=MemberInfoResponse.model_validate(member_entity)
    )


@router.put("/modify", response_class=JSONResponse, response_model=MemberModifyResponseWrapper)
async def update(
    payload: LoginCheckDep,
    member_modify_request: MemberModifyRequest,
    member_service: MemberServiceDep
):
    """현재 로그인 유저의 비밀번호 및 이메일 등의 정보를 수정합니다."""
    member_entity = MemberEntity(**member_modify_request.model_dump(exclude_unset=True))
    member_entity.mid = payload["sub"]
    member_entity = await member_service.modify(member_entity)
    return MemberModifyResponseWrapper(
        data=MemberModifyResponse.model_validate(member_entity)
    )


@router.delete("/delete/{mid}", response_class=JSONResponse, response_model=SuccessResponse)
async def delete(
    payload: AdminCheckDep,
    member_service: MemberServiceDep,
    mid: str
):
    """관리자 권한을 가진 유저가 지정한 사용자를 강제 탈퇴시킵니다."""
    await member_service.delete(mid)
    return SuccessResponse(
        data={"message": f"삭제된 회원의 아이디: {mid}"}
    )
