import logging
from fastapi import APIRouter, Depends
from api.common.auth import LoginCheckDep, verify_access_token
from api.database.config.dto_base import SuccessResponse
from api.v1.gems.models import (
    GemCreateRequest,
    GemUpdateRequest,
    GemResponse,
    GemResponseWrapper,
    GemListResponseWrapper,
    GemChatRequest,
    GemChatResponse,
    GemChatResponseWrapper,
)
from api.v1.gems.services import GemServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gems", tags=["연구 스페이스 (Gems)"], dependencies=[Depends(verify_access_token)])


def _to_gem_response(gem_entity) -> GemResponse:
    """GemEntity -> GemResponse DTO (db_sources str->list)."""
    return GemResponse(
        gem_id=gem_entity.gem_id,
        name=gem_entity.name,
        db_sources=gem_entity.db_sources.split(","),
        system_prompt=gem_entity.system_prompt,
        created_at=gem_entity.created_at,
    )


@router.post("", status_code=201, summary="커스텀 연구 에이전트(Gem) 생성 API")
async def create_gem(
    user: LoginCheckDep,
    request: GemCreateRequest,
    service: GemServiceDep,
) -> GemResponseWrapper:
    """입력받은 이름, 참고 도메인 및 프롬프트 정보를 활용하여 사용자 커스텀 연구 제안 에이전트(Gem)를 생성합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        request (GemCreateRequest): 신규 생성할 Gem의 메타데이터(이름, 도메인 소스, 시스템 프롬프트 등) 정보 DTO.
        service (GemServiceDep): Gem 적재 및 초기화 로직을 수행하는 서비스 의존성.

    Returns:
        GemResponseWrapper: 생성 완료된 커스텀 Gem 상세 데이터를 반환.
    """
    gem_entity = await service.create_gem(
        member_id=user["sub"],
        name=request.name,
        db_sources=request.db_sources,
        system_prompt=request.system_prompt,
    )
    return GemResponseWrapper(data=_to_gem_response(gem_entity))


@router.get("", summary="사용자 소유 커스텀 에이전트(Gem) 목록 조회 API")
async def list_gems(
    user: LoginCheckDep,
    service: GemServiceDep,
) -> GemListResponseWrapper:
    """현재 인증 완료되어 로그인 상태인 유저가 개설했던 모든 사용자 정의 커스텀 에이전트(Gem) 목록을 반환합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        service (GemServiceDep): 사용자의 Gem 데이터베이스 조회를 전담하는 서비스 의존성.

    Returns:
        GemListResponseWrapper: 소유하고 있는 전체 커스텀 에이전트(Gem) 리스트 DTO 객체.
    """
    gems = await service.list_gems(user["sub"])
    return GemListResponseWrapper(data=[_to_gem_response(g) for g in gems])


@router.put("/{gem_id}", summary="커스텀 에이전트(Gem) 정보 수정 API")
async def update_gem(
    user: LoginCheckDep,
    gem_id: str,
    request: GemUpdateRequest,
    service: GemServiceDep,
) -> GemResponseWrapper:
    """지정된 커스텀 에이전트(gem_id)의 메타데이터 항목(이름, 도메인 소스, 시스템 프롬프트 등)을 부분 수정합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        gem_id (str): 수정할 대상 커스텀 Gem의 고유 식별자 ID.
        request (GemUpdateRequest): 수정 반영할 정보 항목 데이터 요청 DTO.
        service (GemServiceDep): Gem 정보 수정을 처리하는 서비스 의존성.

    Returns:
        GemResponseWrapper: 최종 수정 적용된 커스텀 Gem 상세 정보를 반환.
    """
    gem_entity = await service.update_gem(
        member_id=user["sub"],
        gem_id=gem_id,
        name=request.name,
        db_sources=request.db_sources,
        system_prompt=request.system_prompt,
    )
    return GemResponseWrapper(data=_to_gem_response(gem_entity))


@router.delete("/{gem_id}", summary="커스텀 에이전트(Gem) 영구 삭제 API")
async def delete_gem(
    user: LoginCheckDep,
    gem_id: str,
    service: GemServiceDep,
) -> SuccessResponse:
    """지정한 커스텀 에이전트(gem_id) 데이터베이스 정보 및 관련된 대화 히스토리 내역 일체를 영구 삭제합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        gem_id (str): 삭제할 대상 커스텀 Gem의 고유 식별자 ID.
        service (GemServiceDep): Gem 및 관련 데이터 소거를 처리하는 서비스 의존성.

    Returns:
        SuccessResponse: 성공적으로 삭제되었음을 안내하는 성공 응답 객체.
    """
    await service.delete_gem(user["sub"], gem_id)
    return SuccessResponse(data={"message": f"Deleted Gem ID: {gem_id}"})


@router.post("/{gem_id}/chat", summary="커스텀 에이전트(Gem)와의 RAG 대화 수행 API")
async def chat_with_gem(
    user: LoginCheckDep,
    gem_id: str,
    request: GemChatRequest,
    service: GemServiceDep,
) -> GemChatResponseWrapper:
    """사용자가 지정한 커스텀 에이전트(gem_id) 및 특정 대화방(thread_id)을 연결하여 RAG 논문 검색 기반 대화를 진행합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        gem_id (str): 대화할 타겟 커스텀 Gem의 고유 식별자 ID.
        request (GemChatRequest): 질문 내용 및 대화 스레드 ID가 담긴 요청 DTO.
        service (GemServiceDep): 지정된 Gem 전용 룰에 맞춰 RAG 대화 로직을 구동하는 서비스 의존성.

    Returns:
        GemChatResponseWrapper: AI 가 작성한 답변 내용(answer), 논문 세부(papers) 및 검색 출처 목록.
    """
    result = await service.send_message(
        member_id=user["sub"],
        gem_id=gem_id,
        thread_id=request.thread_id,
        message=request.message,
    )
    return GemChatResponseWrapper(
        data=GemChatResponse(
            answer=result["answer"],
            papers=result.get("papers", []),
            sources=result.get("sources", []),
        )
    )


@router.get("/{gem_id}/chat/{thread_id}/messages", summary="커스텀 에이전트(Gem) 대화 히스토리 내역 조회 API")
async def get_gem_messages(
    user: LoginCheckDep,
    gem_id: str,
    thread_id: str,
    service: GemServiceDep,
):
    """특정 커스텀 에이전트(gem_id)와의 특정 대화 스레드(thread_id)에 누적되어 있는 전체 대화 히스토리를 반환합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        gem_id (str): 대화 기록이 연계된 커스텀 Gem 의 고유 식별자 ID.
        thread_id (str): 조회할 대화 세션 스레드의 고유 ID.
        service (GemServiceDep): 대화 내역 데이터베이스 조회를 전담하는 서비스 의존성.

    Returns:
        SuccessResponse: 사용자(user)와 커스텀 에이전트(assistant) 간 주고받은 대화 배열 정보 리스트.
    """
    history = await service.get_messages(user["sub"], gem_id, thread_id)
    return SuccessResponse(data=history)
