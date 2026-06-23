import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def override_auth_dependencies():
    """테스트 시 JWT 인증 의존성을 모의 페이로드로 자동 오버라이딩합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}
    yield
    app.dependency_overrides.clear()


# =====================================================================
# Authentication (Auth) Endpoint Tests
# =====================================================================

@patch("api.v1.auth.services.AuthService.login")
def test_auth_login_endpoint_success(mock_login):
    """OAuth2 호환 로그인 성공 시 토큰 발급 API를 테스트합니다."""
    mock_login.return_value = {
        "access_token": "mocked-jwt-token",
        "token_type": "bearer",
        "username": "test-user",
        "role": "ROLE_USER"
    }

    # OAuth2 Password Form 형식 (x-www-form-urlencoded)
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test-user", "password": "password123"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["access_token"] == "mocked-jwt-token"
    assert json_data["token_type"] == "bearer"
    assert json_data["username"] == "test-user"
    assert json_data["role"] == "ROLE_USER"
    mock_login.assert_called_once_with("test-user", "password123")


@patch("api.v1.auth.services.AuthService.login")
def test_auth_login_endpoint_failure(mock_login):
    """OAuth2 로그인 실패 시 (비즈니스 예외 발생) 400 에러를 반환하는지 테스트합니다."""
    from api.common.exceptions import BusinessException
    mock_login.side_effect = BusinessException("비밀번호가 일치하지 않습니다.", error_code="AUTH_FAILED")

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test-user", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    json_data = response.json()
    assert json_data["status"] == "error"
    assert "비밀번호가 일치하지 않습니다." in json_data["message"]
    mock_login.assert_called_once_with("test-user", "wrongpassword")


def test_auth_me_endpoint_success():
    """인증된 상태에서 현재 토큰 소유자의 정보 조회 API를 테스트합니다."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["username"] == "test-user"
    assert json_data["data"]["role"] == "ROLE_USER"


def test_auth_me_endpoint_unauthorized():
    """인증되지 않은 상태(토큰 없음)에서 내 정보 조회 시 401 에러를 반환하는지 테스트합니다."""
    from api.common.auth import verify_access_token
    from fastapi import HTTPException, status
    
    # verify_access_token이 401 예외를 던지도록 오버라이딩
    def mock_verify_failed():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing"
        )
        
    app.dependency_overrides[verify_access_token] = mock_verify_failed
    try:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        json_data = response.json()
        assert json_data["status"] == "error"
        assert "Token is missing" in json_data["message"]
    finally:
        app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}


def test_auth_admin_only_endpoint_success():
    """관리자 권한을 가진 경우 관리자 전용 리소스 조회를 테스트합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "admin-user", "mrole": "ROLE_ADMIN"}
    try:
        response = client.get("/api/v1/auth/admin-only")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"
        assert "Hello Admin 'admin-user'!" in json_data["data"]["message"]
    finally:
        app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}


def test_auth_admin_only_endpoint_forbidden():
    """일반 사용자 권한으로 관리자 전용 리소스 접근 시 403 Forbidden 에러를 반환하는지 테스트합니다."""
    from api.common.auth import verify_access_token
    app.dependency_overrides[verify_access_token] = lambda: {"sub": "regular-user", "mrole": "ROLE_USER"}
    try:
        response = client.get("/api/v1/auth/admin-only")
        assert response.status_code == 403
        json_data = response.json()
        assert json_data["status"] == "error"
        assert "Required roles:" in json_data["message"]
    finally:
        app.dependency_overrides[verify_access_token] = lambda: {"sub": "test-user", "mrole": "ROLE_USER"}
