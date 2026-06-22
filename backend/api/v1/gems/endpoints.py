import logging
from fastapi import APIRouter
from api.common.auth import LoginCheckDep
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

router = APIRouter(prefix="/gems", tags=["gems"])


def _to_gem_response(gem_entity) -> GemResponse:
    """GemEntity -> GemResponse DTO (db_sources str->list)."""
    return GemResponse(
        gem_id=gem_entity.gem_id,
        name=gem_entity.name,
        db_sources=gem_entity.db_sources.split(","),
        system_prompt=gem_entity.system_prompt,
        created_at=gem_entity.created_at,
    )


@router.post("", status_code=201)
async def create_gem(
    user: LoginCheckDep,
    request: GemCreateRequest,
    service: GemServiceDep,
) -> GemResponseWrapper:
    """Create a new Gem. (F-03-A-1)"""
    gem_entity = await service.create_gem(
        member_id=user["sub"],
        name=request.name,
        db_sources=request.db_sources,
        system_prompt=request.system_prompt,
    )
    return GemResponseWrapper(data=_to_gem_response(gem_entity))


@router.get("")
async def list_gems(
    user: LoginCheckDep,
    service: GemServiceDep,
) -> GemListResponseWrapper:
    """List all Gems for current user. (F-03-A-2)"""
    gems = await service.list_gems(user["sub"])
    return GemListResponseWrapper(data=[_to_gem_response(g) for g in gems])


@router.put("/{gem_id}")
async def update_gem(
    user: LoginCheckDep,
    gem_id: str,
    request: GemUpdateRequest,
    service: GemServiceDep,
) -> GemResponseWrapper:
    """Update a Gem (partial update - only provided fields are changed)."""
    gem_entity = await service.update_gem(
        member_id=user["sub"],
        gem_id=gem_id,
        name=request.name,
        db_sources=request.db_sources,
        system_prompt=request.system_prompt,
    )
    return GemResponseWrapper(data=_to_gem_response(gem_entity))


@router.delete("/{gem_id}")
async def delete_gem(
    user: LoginCheckDep,
    gem_id: str,
    service: GemServiceDep,
) -> SuccessResponse:
    """Delete a Gem."""
    await service.delete_gem(user["sub"], gem_id)
    return SuccessResponse(data={"message": f"Deleted Gem ID: {gem_id}"})


@router.post("/{gem_id}/chat")
async def chat_with_gem(
    user: LoginCheckDep,
    gem_id: str,
    request: GemChatRequest,
    service: GemServiceDep,
) -> GemChatResponseWrapper:
    """Chat with a specific Gem. (F-03-A-3)"""
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


@router.get("/{gem_id}/chat/{thread_id}/messages")
async def get_gem_messages(
    user: LoginCheckDep,
    gem_id: str,
    thread_id: str,
    service: GemServiceDep,
):
    """Get chat history for a Gem thread."""
    history = await service.get_messages(user["sub"], gem_id, thread_id)
    return SuccessResponse(data=history)
