import logging
from typing import Annotated, Optional
from fastapi import APIRouter, File, UploadFile, Form, Depends
from api.common.auth import LoginCheckDep, verify_access_token
from api.database.config.dto_base import SuccessResponse
from api.v1.defense_arena.models import (
    UploadResponse,
    PeerReviewReport,
    HypothesisRequest,
    HypothesisVerificationResult,
    DefenseChatRequest,
    DefenseChatResponse,
    SavedSessionDTO,
    SavedSessionDetailResponse
)
from api.v1.defense_arena.services import DefenseArenaService, DefenseArenaServiceDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/defense-arena", tags=["모의 디펜스 아레나"], dependencies=[Depends(verify_access_token)])


@router.post("/upload-isolated", status_code=201, summary="보안 격리 구역 PDF 업로드 및 청킹 API")
async def upload_isolated_pdf(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    file: UploadFile = File(...)
) -> SuccessResponse:
    """기밀 유지를 보장하는 가상 보안 격리 샌드박스 영역에 PDF 문서를 업로드하고 문서를 분할하여 벡터 임베딩을 수행합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        file (UploadFile): 업로드할 PDF 파일 객체.
        service (DefenseArenaServiceDep): 격리 업로드 및 임베딩 처리를 위임받는 서비스 의존성.

    Returns:
        SuccessResponse: 임시 생성된 세션 ID(session_id) 및 파일명, 추출된 텍스트 청크 개수 정보.
    """
    result = await service.process_pdf_upload(file, mid=user["sub"])
    return SuccessResponse(data=UploadResponse(
        session_id=result["session_id"],
        file_name=result["file_name"],
        chunk_count=result["chunk_count"]
    ))


@router.post("/peer-review", summary="종합 학술 피어리뷰 보고서 생성 API")
async def run_academic_peer_review(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    session_id: str = Form(...),
    target_journal: str = Form(...)
) -> SuccessResponse:
    """방법론 심사, 신규성 심사, 학술 문체 교정 등 3대 특화 에이전트가 순차 분석 및 교정하여 종합 피어리뷰 리포트(Peer Review Report)를 자동 빌드합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        session_id (str): 격리 분석이 완료된 PDF 세션의 UUID 식별자 ID.
        target_journal (str): 투고 대상 학술지/학회 명 정보.
        service (DefenseArenaServiceDep): 멀티 에이전트 워크플로우를 실행하고 취합하는 서비스 의존성.

    Returns:
        SuccessResponse: 취합 완료된 종합 학술 피어리뷰 평가 보고서 내용 DTO.
    """
    report = await service.run_peer_review(session_id, target_journal, mid=user["sub"])
    return SuccessResponse(data=report)


@router.post("/verify-hypothesis", summary="학술 가설 다수결/자가일관성 검증 API")
async def verify_hypothesis(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    session_id: str = Form(...),
    hypothesis: str = Form(...)
) -> SuccessResponse:
    """사용자가 제시한 연구 가설(hypothesis)을 임베딩 벡터 데이터베이스에서 교차 투표하여 다수결 및 자아-일관성(Self-Consistency) 기법에 의거해 참/거짓 여부를 판정합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        session_id (str): 가설을 검증할 격리 샌드박스 세션의 UUID 식별자 ID.
        hypothesis (str): 검증을 희망하는 학술적 연구 가설 설명 텍스트.
        service (DefenseArenaServiceDep): RAG 기반 셀프 컨시스턴시 가설 투표 알고리즘을 구동하는 서비스 의존성.

    Returns:
        SuccessResponse: 가설 검증 통계(투표율, 신뢰 지수) 및 최종 판정 내용.
    """
    result = await service.verify_hypothesis(session_id, hypothesis, mid=user["sub"])
    return SuccessResponse(data=result)


@router.post("/defense/chat", summary="모의 디펜스 심사위원 반론 및 질의응답 API")
async def defense_chat_arena(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    session_id: str = Form(...),
    user_response: Optional[str] = Form(None)
) -> SuccessResponse:
    """가상의 엄격한 저널 심사위원 에이전트가 던지는 비판적 질문에 대응하여 사용자 답변을 검증하고, 모의 디펜스 채점 및 평가 피드백을 진행합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        session_id (str): 모의 디펜스가 진행 중인 격리 PDF 세션 UUID 식별자 ID.
        user_response (Optional[str]): 심사위원 질문에 대응하는 사용자의 반론/답변 텍스트 (최초 시작 시에는 None).
        service (DefenseArenaServiceDep): 심사위원 프롬프트 상태 및 대화 히스토리 평가를 조율하는 서비스 의존성.

    Returns:
        SuccessResponse: 다음 심사위원의 비판적 질문 메시지 또는 최종 디펜스 스코어 성적표 데이터.
    """
    response = await service.process_defense_chat(session_id, user_response, mid=user["sub"])
    return SuccessResponse(data=response)


@router.post("/keep-alive", summary="보안 세션 만료 시간 연장 (Ping) API")
async def keep_alive_session(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    session_id: str = Form(...)
) -> SuccessResponse:
    """보안 격리 세션의 마지막 활동 시각을 현재 시각으로 갱신하여 30분 만료를 연장합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        session_id (str): 세션 ID.
        service (DefenseArenaServiceDep): 서비스 의존성.

    Returns:
        SuccessResponse: 연장 성공 상태.
    """
    await service.extend_session_activity(session_id, mid=user["sub"])
    return SuccessResponse(data={"status": "extended"})


@router.post("/translate", summary="영어 학술 텍스트 한국어 번역 API")
async def translate_text(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    text: str = Form(...)
) -> SuccessResponse:
    """영문으로 구성된 학술 심사평 또는 대화 텍스트를 고품질 한국어로 번역합니다.

    Args:
        user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.
        text (str): 번역할 영문 텍스트.
        service (DefenseArenaServiceDep): 서비스 의존성.

    Returns:
        SuccessResponse: 번역된 텍스트.
    """
    translated = await service.translate_text(text)
    return SuccessResponse(data={"translated_text": translated})


@router.get("/history", summary="보안 세션 보관함 리스트 조회 API")
async def list_history_sessions(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep
) -> SuccessResponse:
    """로그인한 사용자의 아카이빙된 디펜스 아레나 세션 기록 목록을 반환합니다."""
    history = await service.list_saved_sessions(mid=user["sub"])
    return SuccessResponse(data=history)


@router.get("/history/{session_id}", summary="보관 세션 상세 복원 조회 API")
async def get_history_session_detail(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    session_id: str
) -> SuccessResponse:
    """지정한 보관 세션의 상세 분석 리포트 및 과거 대화 전체 로그를 불러옵니다."""
    detail = await service.get_session_detail(session_id, mid=user["sub"])
    return SuccessResponse(data=detail)


@router.delete("/history/{session_id}", summary="보관 세션 삭제 API")
async def delete_history_session(
    user: LoginCheckDep,
    service: DefenseArenaServiceDep,
    session_id: str
) -> SuccessResponse:
    """보관함에서 특정 세션 분석 기록을 완전히 영구 삭제합니다."""
    await service.defense_arena_dao.delete_session(session_id)
    return SuccessResponse(data={"status": "deleted"})



