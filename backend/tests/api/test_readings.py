from __future__ import annotations

from datetime import date
from fastapi.testclient import TestClient


def test_create_reading(client: TestClient, auth_token: str):
    """测试创建阅读记录接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    member_response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )
    member_id = member_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建阅读记录
    response = client.post(
        "/v1/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "family_id": family_id,
            "member_id": member_id,
            "book_meta_id": book_meta_id,
            "status": "reading",
            "progress_type": "page",
            "progress_value": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["family_id"] == family_id
    assert data["member_id"] == member_id
    assert data["book_meta_id"] == book_meta_id
    assert data["status"] == "reading"
    assert data["progress_type"] == "page"
    assert data["progress_value"] == 10


def test_create_reading_with_book_copy(client: TestClient, auth_token: str):
    """测试创建阅读记录并同时创建书籍副本"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    member_response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )
    member_id = member_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建阅读记录并同时创建书籍副本
    response = client.post(
        "/v1/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "family_id": family_id,
            "member_id": member_id,
            "book_meta_id": book_meta_id,
            "status": "reading",
            "progress_type": "page",
            "progress_value": 10,
            "create_book_copy": {
                "acquired_type": "purchase",
                "acquired_at": str(date.today()),
                "acquired_from": "Amazon",
                "price_cny": 59.9,
                "note": "测试书籍副本"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["book_copy_id"] is not None


def test_patch_reading(client: TestClient, auth_token: str):
    """测试更新阅读记录接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    member_response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )
    member_id = member_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建阅读记录
    create_response = client.post(
        "/v1/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "family_id": family_id,
            "member_id": member_id,
            "book_meta_id": book_meta_id,
            "status": "reading",
            "progress_type": "page",
            "progress_value": 10
        }
    )
    reading_id = create_response.json()["id"]

    # 更新阅读记录
    response = client.patch(
        f"/v1/readings/{reading_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "status": "finished",
            "progress_value": 100,
            "finished_on": str(date.today()),
            "note": "测试更新"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reading_id
    assert data["status"] == "finished"
    assert data["progress_value"] == 100
    assert data["note"] == "测试更新"


def test_list_readings(client: TestClient, auth_token: str):
    """测试获取阅读记录列表接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    member_response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )
    member_id = member_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建阅读记录
    client.post(
        "/v1/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "family_id": family_id,
            "member_id": member_id,
            "book_meta_id": book_meta_id,
            "status": "reading",
            "progress_type": "page",
            "progress_value": 10
        }
    )

    # 获取阅读记录列表
    response = client.get(
        f"/v1/families/{family_id}/readings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_reading(client: TestClient, auth_token: str):
    """测试获取单个阅读记录详情接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    member_response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )
    member_id = member_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建阅读记录
    create_response = client.post(
        "/v1/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "family_id": family_id,
            "member_id": member_id,
            "book_meta_id": book_meta_id,
            "status": "reading",
            "progress_type": "page",
            "progress_value": 10
        }
    )
    reading_id = create_response.json()["id"]

    # 获取单个阅读记录详情
    response = client.get(
        f"/v1/readings/{reading_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reading_id
    assert data["family_id"] == family_id
    assert data["member_id"] == member_id
    assert data["book_meta_id"] == book_meta_id
    assert data["status"] == "reading"
    assert "book" in data
    assert "title" in data["book"]


def test_get_reading_not_found(client: TestClient, auth_token: str):
    """测试获取不存在的阅读记录"""
    response = client.get(
        "/v1/readings/99999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


def test_list_readings_with_filters(client: TestClient, auth_token: str):
    """测试带过滤条件的阅读记录列表接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    member_response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )
    member_id = member_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建阅读记录
    client.post(
        "/v1/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "family_id": family_id,
            "member_id": member_id,
            "book_meta_id": book_meta_id,
            "status": "reading",
            "progress_type": "page",
            "progress_value": 10
        }
    )

    # 带过滤条件获取阅读记录列表
    response = client.get(
        f"/v1/families/{family_id}/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        params={"member_id": member_id, "status_filter": "reading"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_delete_reading(client: TestClient, auth_token: str):
    """测试删除阅读记录接口"""
    # 先创建家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    member_response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )
    member_id = member_response.json()["id"]

    # 解析书籍
    book_response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    book_meta_id = book_response.json()["id"]

    # 创建阅读记录
    create_response = client.post(
        "/v1/readings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "family_id": family_id,
            "member_id": member_id,
            "book_meta_id": book_meta_id,
            "status": "reading",
            "progress_type": "page",
            "progress_value": 10
        }
    )
    reading_id = create_response.json()["id"]

    # 删除阅读记录
    response = client.delete(
        f"/v1/readings/{reading_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204

    # 确认记录已被删除
    response = client.get(
        f"/v1/families/{family_id}/readings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    data = response.json()
    assert not any(r["id"] == reading_id for r in data)