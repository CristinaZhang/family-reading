from __future__ import annotations

import pytest
from app.auth import _parse_token, get_current_user
from app.db.models import User
from fastapi.testclient import TestClient
from sqlmodel import Session


def test_parse_token():
    """测试token解析函数"""
    # 测试有效的token
    assert _parse_token("u:1") == 1
    assert _parse_token("u:123") == 123

    # 测试无效的token
    assert _parse_token(None) is None
    assert _parse_token("") is None
    assert _parse_token("invalid") is None
    assert _parse_token("u:") is None
    assert _parse_token("u:abc") is None
    assert _parse_token("u:1.2") is None


def test_get_current_user_no_authorization(client: TestClient):
    """测试缺少Authorization头的情况"""
    # 创建一个需要认证的请求
    response = client.get("/v1/families")
    assert response.status_code == 401
    assert "Missing bearer token" in response.json()["detail"]


def test_get_current_user_invalid_authorization_format(client: TestClient):
    """测试Authorization头格式错误的情况"""
    # 创建一个Authorization头格式错误的请求
    response = client.get(
        "/v1/families",
        headers={"Authorization": "Invalid format"}
    )
    assert response.status_code == 401
    assert "Missing bearer token" in response.json()["detail"]


def test_get_current_user_invalid_token(client: TestClient):
    """测试无效token的情况"""
    # 创建一个带有无效token的请求
    response = client.get(
        "/v1/families",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_get_current_user_nonexistent_user(client: TestClient):
    """测试用户不存在的情况"""
    # 创建一个带有不存在用户ID的token的请求
    response = client.get(
        "/v1/families",
        headers={"Authorization": "Bearer u:999999"}
    )
    assert response.status_code == 401
    assert "User not found" in response.json()["detail"]