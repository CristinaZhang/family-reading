from __future__ import annotations

from fastapi.testclient import TestClient


def test_resolve_book(client: TestClient, auth_token: str):
    """测试解析书籍接口"""
    response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}  # 示例ISBN
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "isbn13" in data
    assert "title" in data
    assert "authors" in data
    assert isinstance(data["authors"], list)
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_resolve_book_invalid_isbn(client: TestClient, auth_token: str):
    """测试解析书籍接口 - 无效ISBN"""
    response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "invalid_isbn"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid isbn"