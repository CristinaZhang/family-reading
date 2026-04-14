from __future__ import annotations

from fastapi.testclient import TestClient


def test_dev_login(client: TestClient):
    """测试开发登录接口"""
    response = client.post(
        "/v1/auth/dev/login",
        json={"openid": "test_user_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert "id" in data["user"]
    assert data["user"]["openid"] == "test_user_123"


def test_dev_login_empty_openid(client: TestClient):
    """测试开发登录接口 - 空openid"""
    response = client.post(
        "/v1/auth/dev/login",
        json={"openid": ""}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "openid required"


def test_wechat_login(client: TestClient):
    """测试微信登录接口"""
    # 注意：这里使用的是测试code，实际测试时会返回错误
    # 因为我们没有配置真实的微信小程序AppID和AppSecret
    response = client.post(
        "/v1/auth/wechat/login",
        json={"code": "test_code"}
    )
    # 预期返回400或500错误，因为测试code无效
    assert response.status_code in [400, 500]


def test_health_check(client: TestClient):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}