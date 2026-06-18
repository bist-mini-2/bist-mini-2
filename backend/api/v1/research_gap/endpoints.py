import logging
from fastapi import APIRouter, BackgroundTasks, status

from api.database.config.dto_base import SuccessResponse
from api.common.auth import LoginCheckDep
from api.v1.research_gap.models import AnalyzeRequest, BulkDeleteRequest
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


@router.post(
    "/tasks/{task_id}/translate",
    response_model=SuccessResponse,
    summary="연구 공백 분석 결과 한글 번역 및 캐싱"
)
async def translate_task(
    task_id: str,
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """영문으로 완료된 특정 배치 분석 태스크 결과를 한국어로 번역하고 서버에 영구 캐싱 보관합니다."""
    mid = current_user["sub"]
    translated = await service.translate_matrix(task_id, mid)
    return SuccessResponse(data=translated)


@router.get(
    "/tasks",
    response_model=SuccessResponse,
    summary="사용자의 모든 배치 분석 작업 이력 조회"
)
async def list_user_tasks(
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """현재 로그인한 사용자가 등록했던 모든 비동기 분석 배치 작업 이력 리스트를 반환합니다."""
    mid = current_user["sub"]
    tasks_list = await service.list_user_tasks(mid)
    return SuccessResponse(data=tasks_list)


@router.delete(
    "/tasks/{task_id}",
    response_model=SuccessResponse,
    summary="특정 배치 분석 작업 이력 삭제"
)
async def delete_user_task(
    task_id: str,
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """현재 로그인한 사용자가 소유한 특정 배치 분석 작업 데이터를 삭제합니다."""
    mid = current_user["sub"]
    await service.delete_user_task(task_id, mid)
    return SuccessResponse(data={"deleted": True})


@router.post(
    "/tasks/bulk-delete",
    response_model=SuccessResponse,
    summary="여러 배치 분석 작업 이력 선택 삭제"
)
async def bulk_delete_user_tasks(
    payload: BulkDeleteRequest,
    service: ResearchGapServiceDep,
    current_user: LoginCheckDep
):
    """현재 로그인한 사용자가 소유한 여러 배치 분석 작업 데이터를 일괄 삭제합니다."""
    mid = current_user["sub"]
    deleted_count = await service.delete_user_tasks(payload.task_ids, mid)
    return SuccessResponse(data={"deleted_count": deleted_count})







