import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def override_auth_dependency():
    """테스트 시 JWT 인증 의존성을 모의 페이로드로 자동 오버라이딩합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}
    yield
    app.dependency_overrides.clear()


# =====================================================================
# 1. API Endpoints Test Cases (FastAPI Routing & DTO Validation)
# =====================================================================

@patch("api.v1.research_gap.services.ResearchGapService.start_analysis")
def test_start_analysis_endpoint(mock_start_analysis):
    """비동기 분석 요청 API가 201 상태코드와 생성된 태스크 ID를 정상 반환하는지 테스트합니다."""
    mock_start_analysis.return_value = "mocked-task-uuid"

    payload = {"domain": "cs", "query": "transformer dynamics"}
    response = client.post("/api/v1/research-gap/analyze", json=payload)

    assert response.status_code == 201
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["task_id"] == "mocked-task-uuid"
    from unittest.mock import ANY
    mock_start_analysis.assert_called_once_with("cs", "transformer dynamics", ANY, "test-user")


def test_start_analysis_invalid_domain_validation_error():
    """지원하지 않는 도메인 명을 전송할 시 400 Bad Request가 발생하는지 테스트합니다."""
    payload = {"domain": "invalid_domain", "query": "transformer"}
    response = client.post("/api/v1/research-gap/analyze", json=payload)

    assert response.status_code == 400
    json_data = response.json()
    assert json_data["status"] == "error"


@patch("api.v1.research_gap.services.ResearchGapService.get_task_status")
def test_get_task_status_endpoint(mock_get_status):
    """배치 작업 상태 조회 API가 정상 상태 조회를 수행하는지 테스트합니다."""
    mock_get_status.return_value = {
        "task_id": "test-uuid",
        "domain": "cs",
        "query": "transformer",
        "status": "RUNNING",
        "progress": 40,
        "created_at": "2026-06-17T00:00:00",
        "updated_at": "2026-06-17T00:00:00"
      }

    response = client.get("/api/v1/research-gap/tasks/test-uuid")

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["progress"] == 40
    assert json_data["data"]["status"] == "RUNNING"
    mock_get_status.assert_called_once_with("test-uuid", "test-user")


@patch("api.v1.research_gap.services.ResearchGapService.get_task_status")
def test_get_task_status_not_found(mock_get_status):
    """존재하지 않는 태스크 조회 시 404 에러가 리턴되는지 테스트합니다."""
    from api.common.exceptions import TaskNotFoundError
    mock_get_status.side_effect = TaskNotFoundError("요청하신 태스크 ID를 찾을 수 없습니다: missing-uuid")

    response = client.get("/api/v1/research-gap/tasks/missing-uuid")

    assert response.status_code == 404
    json_data = response.json()
    assert json_data["status"] == "error"


@patch("api.v1.research_gap.services.ResearchGapService.get_task_result")
def test_get_task_result_endpoint(mock_get_result):
    """분석 결과 조회 API가 최종 매트릭스를 반환하는지 테스트합니다."""
    mock_get_result.return_value = {
        "task_id": "test-uuid",
        "status": "COMPLETED",
        "progress": 100,
        "result": {
            "papers": [
                {
                    "title": "A Mock Paper",
                    "arxiv_id": "1234.5678",
                    "problems_solved": ["Mock problem"],
                    "limitations": ["Mock limitation"]
                }
            ],
            "common_limitations": ["Mock common limit"],
            "suggested_directions": ["Mock suggestion"]
        },
        "error_message": None
    }

    response = client.get("/api/v1/research-gap/tasks/test-uuid/result")

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["result"]["papers"][0]["arxiv_id"] == "1234.5678"
    mock_get_result.assert_called_once_with("test-uuid", "test-user")


# =====================================================================
# 2. Service Layer Unit Test Case (ResearchGapService & Dao Orchestration)
# =====================================================================

@pytest.mark.anyio
async def test_start_analysis_service_logic():
    """ResearchGapService.start_analysis 비즈니스 로직이 DAO를 생성하고 백그라운드 태스크를 올바르게 연결하는지 테스트합니다."""
    mock_dao = MagicMock()
    mock_dao.create_task = AsyncMock(return_value=None)
    mock_bg_tasks = MagicMock()

    from api.v1.research_gap.services import ResearchGapService
    service = ResearchGapService(research_gap_dao=mock_dao)

    task_id = await service.start_analysis(
        domain="cs",
        query="neural evolutionary computation",
        background_tasks=mock_bg_tasks,
        mid="test-user"
    )

    assert task_id is not None
    assert isinstance(task_id, str)
    mock_dao.create_task.assert_called_once_with(task_id, "cs", "neural evolutionary computation", "test-user")
    mock_bg_tasks.add_task.assert_called_once()


def test_unauthorized_access():
    """인증 토큰이 없을 시 401 Unauthorized를 리턴하는지 테스트합니다."""
    # 의존성 오버라이드를 임시 해제하여 실제 401 반응 확인
    app.dependency_overrides.clear()
    try:
        response = client.get("/api/v1/research-gap/tasks/test-uuid")
        assert response.status_code == 401
        json_data = response.json()
        assert json_data["status"] == "error"
        assert "Token is missing" in json_data["message"]
    finally:
        # 다른 테스트를 위해 재등록
        from api.common.auth import verify_access_token
        app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}


@patch("api.v1.research_gap.services.ResearchGapService.translate_matrix")
def test_translate_matrix_endpoint(mock_translate_matrix):
    """결과 번역 API가 정상적으로 번역된 결과를 반환하는지 테스트합니다."""
    mock_translate_matrix.return_value = {
        "papers": [
            {
                "title": "번역된 제목",
                "arxiv_id": "1234.5678",
                "problems_solved": ["해결된 문제"],
                "limitations": ["한계점"]
            }
        ],
        "common_limitations": ["공통 한계점"],
        "suggested_directions": ["추천 방향"]
    }

    response = client.post("/api/v1/research-gap/tasks/test-uuid/translate")

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["papers"][0]["title"] == "번역된 제목"
    mock_translate_matrix.assert_called_once_with("test-uuid", "test-user")

