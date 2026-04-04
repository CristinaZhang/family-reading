from __future__ import annotations

from fastapi.testclient import TestClient


def test_dashboard(client: TestClient, auth_token: str):
    """测试获取家庭阅读统计数据接口"""
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

    # 获取仪表板数据
    response = client.get(
        f"/v1/families/{family_id}/dashboard",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["family_id"] == family_id
    assert isinstance(data["members"], list)
    assert len(data["members"]) > 0

    # 检查成员数据
    member_data = data["members"][0]
    assert member_data["member_id"] == member_id
    assert member_data["display_name"] == "测试成员"
    assert member_data["reading"] == 1
    assert member_data["finished"] == 0
    assert member_data["paused"] == 0
    assert member_data["rereading"] == 0
    assert member_data["wishlist"] == 0