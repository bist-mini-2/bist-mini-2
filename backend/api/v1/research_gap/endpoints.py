import logging
from fastapi import APIRouter, BackgroundTasks, status, Depends

from api.database.config.dto_base import SuccessResponse
from api.common.auth import LoginCheckDep, verify_access_token
from api.v1.research_gap.models import AnalyzeRequest, BulkDeleteRequest
from api.v1.research_gap.services import ResearchGapServiceDep

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/research-gap", tags=["Research Gap Analyzer"], dependencies=[Depends(verify_access_token)])


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
    """비동기 방식으로 동작하는 대규모 문헌 비교 분석 배치 작업을 생성하고 예약을 등록합니다.

    Args:
        payload (AnalyzeRequest): 문헌 분석 요청 도메인(cs/bio) 및 주제 검색어가 담긴 DTO.
        background_tasks (BackgroundTasks): 비동기 백그라운드 태스크 처리를 위한 FastAPI 백그라운드 작업 관리자.
        service (ResearchGapServiceDep): 분석 요청 등록 및 스케줄링을 담당하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 예약 등록된 비동기 분석 작업 식별자 ID(task_id) 정보를 반환.
    """
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
    """특정 비동기 배치 작업(task_id)의 현재 진행 상태(PENDING, RUNNING, COMPLETED, FAILED) 및 가동 진행도(%)를 실시간 확인합니다.

    Args:
        task_id (str): 상태를 조회할 배치 작업의 UUID 식별자.
        service (ResearchGapServiceDep): 배치 작업 정보 및 이력을 담당하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 해당 배치 분석 작업의 상세 상태 및 진척율 데이터를 반환.
    """
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
    """분석 완료(COMPLETED) 상태인 배치 작업의 결과물(비교 대상 논문 매트릭스 목록, 공통 한계점, 신규 연구 제안 리포트)을 가져옵니다.

    Args:
        task_id (str): 결과 데이터를 불러올 완료된 배치 작업의 UUID 식별자.
        service (ResearchGapServiceDep): 분석 데이터 조회를 수행하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 완성된 논문 매트릭스 표 및 합성 리포트 원본 데이터를 반환.
    """
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
    """완료된 영어 논문 분석 결과 데이터(매트릭스 내용 및 제안 리포트)를 한국어로 기계 번역하고 캐싱 처리합니다.

    Args:
        task_id (str): 번역을 처리하고 캐시할 배치 작업의 UUID 식별자.
        service (ResearchGapServiceDep): AI 번역 및 번역 데이터 영구 캐시 처리를 담당하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 한국어로 번역 반영된 결과 리포트 정보 데이터를 반환.
    """
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
    """현재 로그인한 사용자가 과거에 의뢰하여 실행했던 모든 문헌 비교 분석 배치 작업 리스트를 최신 이력 순으로 반환합니다.

    Args:
        service (ResearchGapServiceDep): 사용자의 분석 이력을 관리하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 사용자의 모든 분석 배치 작업 이력 리스트 데이터를 반환.
    """
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
    """사용자가 생성하여 보유 중인 특정 문헌 분석 배치 작업(task_id)과 관련된 모든 메타 및 결과 데이터를 영구적으로 삭제합니다.

    Args:
        task_id (str): 데이터베이스 및 파일 시스템에서 삭제할 배치 작업 식별자.
        service (ResearchGapServiceDep): 데이터 삭제 처리를 전담하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 삭제 성공 상태 여부 데이터를 반환.
    """
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
    """사용자가 선택한 복수의 배치 분석 작업 식별자(task_ids)들을 일괄로 영구 데이터베이스에서 제거합니다.

    Args:
        payload (BulkDeleteRequest): 일괄 삭제 처리할 복수의 task_id 배열 정보 DTO.
        service (ResearchGapServiceDep): 일괄 삭제 트랜잭션을 수행하는 서비스 의존성.
        current_user (LoginCheckDep): 인증이 완료된 현재 로그인 사용자의 JWT 페이로드 정보.

    Returns:
        SuccessResponse: 최종 일괄 삭제 처리된 개수 정보를 반환.
    """
    mid = current_user["sub"]
    deleted_count = await service.delete_user_tasks(payload.task_ids, mid)
    return SuccessResponse(data={"deleted_count": deleted_count})







