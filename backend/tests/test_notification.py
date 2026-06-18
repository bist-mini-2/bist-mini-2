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


@patch("api.v1.notification.services.NotificationService.list_notifications")
def test_list_notifications(mock_list):
    """사용자 알림 목록 조회 API가 200 상태코드를 정상 반환하는지 테스트합니다."""
    from datetime import datetime, timezone
    mock_list.return_value = [
        MagicMock(
            id="notif-1",
            mid="test-user",
            title="테스트 알림",
            message="메시지",
            type="info",
            task_id="task-1",
            read=False,
            created_at=datetime.now(timezone.utc)
        )
    ]

    response = client.get("/api/v1/notification")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["id"] == "notif-1"


@patch("api.v1.notification.services.NotificationService.mark_as_read")
def test_mark_as_read(mock_read):
    """개별 알림 읽음 처리 API 테스트"""
    mock_read.return_value = True

    response = client.put("/api/v1/notification/notif-1/read")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["success"] is True


@patch("api.v1.notification.services.NotificationService.mark_all_as_read")
def test_mark_all_as_read(mock_read_all):
    """전체 알림 읽음 처리 API 테스트"""
    mock_read_all.return_value = None

    response = client.put("/api/v1/notification/read-all")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["success"] is True


@patch("api.v1.notification.services.NotificationService.delete_notification")
def test_delete_notification(mock_delete):
    """개별 알림 삭제 API 테스트"""
    mock_delete.return_value = True

    response = client.delete("/api/v1/notification/notif-1")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["success"] is True


@patch("api.v1.notification.services.NotificationService.delete_all_notifications")
def test_delete_all_notifications(mock_delete_all):
    """전체 알림 삭제 API 테스트"""
    mock_delete_all.return_value = None

    response = client.delete("/api/v1/notification")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["success"] is True
