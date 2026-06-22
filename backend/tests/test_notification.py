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


@pytest.mark.anyio
async def test_broadcaster_shutdown():
    """NotificationBroadcaster의 종료(close) 처리 및 큐 대기 해제 기능 테스트"""
    import asyncio
    from api.v1.notification.notifier import NotificationBroadcaster
    broadcaster = NotificationBroadcaster()
    
    # 1. 초기 상태 확인
    assert not broadcaster.is_shutdown
    
    # 2. 리스너 구독 등록
    queue = broadcaster.subscribe()
    assert queue in broadcaster._listeners
    
    # 3. 브로드캐스터 종료 호출
    broadcaster.close()
    assert broadcaster.is_shutdown
    
    # 4. 대기 중인 리스너가 None(종료 센티넬)을 수신했는지 검증
    sentinel = await queue.get()
    assert sentinel is None
    
    # 5. 종료 상태에서 구독한 신규 큐는 None이 즉시 반환되는지 검증
    new_queue = broadcaster.subscribe()
    sentinel2 = await new_queue.get()
    assert sentinel2 is None


@pytest.mark.anyio
async def test_stream_notifications_exits_on_shutdown():
    """서버가 종료될 때(broadcaster.close()) SSE 제너레이터 루프가 정상적으로 종료되는지 테스트"""
    import asyncio
    from api.v1.notification.services import NotificationService
    from api.v1.notification.notifier import notification_broadcaster
    
    # 전역 인스턴스의 종료 상태 리셋
    notification_broadcaster.is_shutdown = False
    
    mock_request = AsyncMock()
    mock_request.is_disconnected.return_value = False
    
    # 모의 DAO 주입
    service = NotificationService(notification_dao=MagicMock())
    
    generator = service.stream_notifications(mock_request, "test-user")
    
    # 비동기로 broadcaster.close() 실행
    async def trigger_shutdown():
        await asyncio.sleep(0.05)
        notification_broadcaster.close()
        
    shutdown_task = asyncio.create_task(trigger_shutdown())
    
    # 제너레이터 소비
    results = []
    async for item in generator:
        results.append(item)
        
    await shutdown_task
    assert notification_broadcaster.is_shutdown
    
    # 전역 인스턴스 상태 복구
    notification_broadcaster.is_shutdown = False

