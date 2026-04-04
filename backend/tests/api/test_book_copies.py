from __future__ import annotations

from datetime import date
from fastapi.testclient import TestClient


def test_create_book_copy(client: TestClient, auth_token: str):
    """测试创建书籍副本接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建书籍副本
    response = client.post(
        f"/v1/families/{family_id}/book_copies",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "book_meta_id": book_meta_id,
            "acquired_type": "purchase",
            "acquired_at": str(date.today()),
            "acquired_from": "Amazon",
            "price_cny": 59.9,
            "note": "测试书籍副本"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["family_id"] == family_id
    assert data["book_meta_id"] == book_meta_id
    assert data["acquired_type"] == "purchase"
    assert data["acquired_from"] == "Amazon"
    assert data["price_cny"] == 59.9
    assert data["note"] == "测试书籍副本"


def test_list_book_copies(client: TestClient, auth_token: str):
    """测试获取书籍副本列表接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建书籍副本
    client.post(
        f"/v1/families/{family_id}/book_copies",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "book_meta_id": book_meta_id,
            "acquired_type": "purchase",
            "acquired_at": str(date.today()),
            "acquired_from": "Amazon",
            "price_cny": 59.9,
            "note": "测试书籍副本"
        }
    )

    # 获取书籍副本列表
    response = client.get(
        f"/v1/families/{family_id}/book_copies",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_book_copies_with_filter(client: TestClient, auth_token: str):
    """测试带过滤条件的书籍副本列表接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建书籍副本
    client.post(
        f"/v1/families/{family_id}/book_copies",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "book_meta_id": book_meta_id,
            "acquired_type": "purchase",
            "acquired_at": str(date.today()),
            "acquired_from": "Amazon",
            "price_cny": 59.9,
            "note": "测试书籍副本"
        }
    )

    # 带过滤条件获取书籍副本列表
    response = client.get(
        f"/v1/families/{family_id}/book_copies",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"book_meta_id": book_meta_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert item["book_meta_id"] == book_meta_id