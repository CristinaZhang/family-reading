from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_family(client: TestClient, auth_token: str):
    """测试创建家庭接口"""
    response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "测试家庭"
    assert "owner_user_id" in data
    assert "created_at" in data


def test_create_family_empty_name(client: TestClient, auth_token: str):
    """测试创建家庭接口 - 空名称"""
    response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": ""}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "name required"


def test_list_families(client: TestClient, auth_token: str):
    """测试获取家庭列表接口"""
    # 先创建一个家庭
    client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )

    # 获取家庭列表
    response = client.get(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_create_member(client: TestClient, auth_token: str):
    """测试添加家庭成员接口"""
    # 先创建一个家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "display_name": "测试成员",
            "avatar_url": "https://example.com/avatar.jpg"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["family_id"] == family_id
    assert data["display_name"] == "测试成员"
    assert data["avatar_url"] == "https://example.com/avatar.jpg"
    assert data["bound_user_id"] is None


def test_create_member_empty_name(client: TestClient, auth_token: str):
    """测试添加家庭成员接口 - 空名称"""
    # 先创建一个家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员（空名称）
    response = client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": ""}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "display_name required"


def test_list_members(client: TestClient, auth_token: str):
    """测试获取家庭成员列表接口"""
    # 先创建一个家庭
    family_response = client.post(
        "/v1/families",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "测试家庭"}
    )
    family_id = family_response.json()["id"]

    # 添加家庭成员
    client.post(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"display_name": "测试成员"}
    )

    # 获取家庭成员列表
    response = client.get(
        f"/v1/families/{family_id}/members",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0