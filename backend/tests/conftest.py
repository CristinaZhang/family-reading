from __future__ import annotations

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.config import settings
from app.db.database import get_session
from app.main import create_app


@pytest.fixture
def test_db():
    # 使用内存SQLite数据库进行测试
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def client(test_db):
    app = create_app()

    # 替换依赖项中的数据库会话
    def override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = override_get_session

    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """获取测试用的认证令牌"""
    response = client.post(
        "/v1/auth/dev/login",
        json={"openid": "test_user"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]