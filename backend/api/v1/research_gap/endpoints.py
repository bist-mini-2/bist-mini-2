import logging
from fastapi import APIRouter, BackgroundTasks, Request, status
from fastapi.responses import StreamingResponse

from api.database.config.dto_base import SuccessResponse
from api.common.auth import LoginCheckDep
from api.v1.research_gap.models import AnalyzeRequest
from api.v1.research_gap.services import ResearchGapServiceDep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research-gap", tags=["Research Gap Analyzer"])


@router.post(
    "/analyze",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="비동기 대규모 문헌 비교 분석 시작"
)
async def start_analysis(
    payload: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """비동기 배치 RAG 분석 작업을 생성하고 예약을 등록합니다. (검증 및 작업 관리는 서비스 레이어에 위임합니다.)"""
    mid = current_user["sub"]
    task_id = await service.start_analysis(payload.domain, payload.query, background_tasks, mid)
    return SuccessResponse(
        data={"task_id": task_id}
    )


@router.get(
    "/tasks/{task_id}",
    response_model=SuccessResponse,
    summary="배치 분석 작업 상태 조회"
)
async def get_task_status(
    task_id: str,
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """배치 작업의 현재 진행 상태(PENDING, RUNNING, COMPLETED, FAILED) 및 진행도(progress %)를 확인합니다."""
    mid = current_user["sub"]
    status_info = await service.get_task_status(task_id, mid)
    return SuccessResponse(data=status_info)


@router.get(
    "/tasks/{task_id}/result",
    response_model=SuccessResponse,
    summary="배치 분석 최종 결과 조회"
)
async def get_task_result(
    task_id: str,
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """완료된 분석 작업의 최종 매트릭스 표 및 합성 연구 방향 리포트 데이터를 획득합니다."""
    mid = current_user["sub"]
    result_info = await service.get_task_result(task_id, mid)
    return SuccessResponse(data=result_info)


@router.get(
    "/stream-notifications",
    summary="실시간 SSE 푸시 알림 수신",
    include_in_schema=False
)
async def stream_notifications(
    request: Request,
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """백그라운드 비동기 연산 완료 소식을 클라이언트에 실시간 푸시하는 SSE(Server-Sent Events) 스트림 엔드포인트입니다."""
    mid = current_user["sub"]
    return StreamingResponse(
        service.stream_notifications(request, mid),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
