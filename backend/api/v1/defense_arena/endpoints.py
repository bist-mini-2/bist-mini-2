import logging
from typing import Annotated, Optional
from fastapi import APIRouter, File, UploadFile, Form, Depends
from api.common.auth import LoginCheckDep
from api.database.config.dto_base import SuccessResponse
from api.v1.defense_arena.models import (
    UploadResponse,
    PeerReviewReport,
    HypothesisRequest,
    HypothesisVerificationResult,
    DefenseChatRequest,
    DefenseChatResponse
)
from api.v1.defense_arena.services import DefenseArenaService, DefenseArenaServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/defense-arena", tags=["defense_arena"])


@router.post("/upload-isolated", status_code=201)
async def upload_isolated_pdf(
    user: LoginCheckDep,
    file: UploadFile = File(...),
    service: DefenseArenaServiceDep = None
) -> SuccessResponse:
    """기밀 유지 보안 격리 샌드박스 영역에 PDF를 임시 업로드하고 임베딩을 수행합니다. (F-02-A-1)"""
    result = await service.process_pdf_upload(file, mid=user["sub"])
    return SuccessResponse(data=UploadResponse(
        session_id=result["session_id"],
        file_name=result["file_name"],
        chunk_count=result["chunk_count"]
    ))


@router.post("/peer-review")
async def run_academic_peer_review(
    user: LoginCheckDep,
    session_id: str = Form(...),
    target_journal: str = Form(...),
    service: DefenseArenaServiceDep = None
) -> SuccessResponse:
    """3대 심층 에이전트(방법론, 신규성, 학술문체)가 교대로 분석한 종합 피어리뷰 리포트를 생성합니다. (F-02-A-3)"""
    report = await service.run_peer_review(session_id, target_journal, mid=user["sub"])
    return SuccessResponse(data=report)


@router.post("/verify-hypothesis")
async def verify_hypothesis(
    user: LoginCheckDep,
    session_id: str = Form(...),
    hypothesis: str = Form(...),
    service: DefenseArenaServiceDep = None
) -> SuccessResponse:
    """자기 일관성(Self-Consistency) 기법에 기반해 RAG 투표를 거쳐 연구 가설을 검증합니다. (F-02-A-4)"""
    result = await service.verify_hypothesis(session_id, hypothesis, mid=user["sub"])
    return SuccessResponse(data=result)


@router.post("/defense/chat")
async def defense_chat_arena(
    user: LoginCheckDep,
    session_id: str = Form(...),
    user_response: Optional[str] = Form(None),
    service: DefenseArenaServiceDep = None
) -> SuccessResponse:
    """가상의 엄격한 심사위원 에이전트와 실시간 모의 디펜스를 주고받으며 채점을 시뮬레이션합니다. (F-02-A-5)"""
    response = await service.process_defense_chat(session_id, user_response, mid=user["sub"])
    return SuccessResponse(data=response)
