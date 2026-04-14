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


def test_resolve_book_isbn10(client: TestClient, auth_token: str):
    """测试解析书籍接口 - ISBN-10格式"""
    response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "0306406152"}  # ISBN-10格式
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "isbn13" in data
    assert data["isbn13"].startswith("978")  # 应该转换为ISBN-13


def test_resolve_book_isbn_with_hyphens(client: TestClient, auth_token: str):
    """测试解析书籍接口 - 带有连字符的ISBN"""
    response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "978-7-5442-7087-8"}  # 带有连字符的ISBN
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "isbn13" in data
    assert "-" not in data["isbn13"]  # 连字符应该被移除


def test_resolve_book_isbn_with_spaces(client: TestClient, auth_token: str):
    """测试解析书籍接口 - 带有空格的ISBN"""
    response = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "978 7 5442 7087 8"}  # 带有空格的ISBN
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "isbn13" in data
    assert " " not in data["isbn13"]  # 空格应该被移除


def test_resolve_book_duplicate_isbn(client: TestClient, auth_token: str):
    """测试解析书籍接口 - 重复解析同一个ISBN"""
    # 第一次解析
    response1 = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    book_id1 = data1["id"]

    # 第二次解析同一个ISBN
    response2 = client.post(
        "/v1/books/resolve",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"isbn": "9787544270878"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    book_id2 = data2["id"]

    # 两次解析应该返回同一个书籍ID（缓存）
    assert book_id1 == book_id2


def test_create_book_only_title(client: TestClient, auth_token: str):
    """测试创建书籍接口 - 只提供标题（直接添加书籍名字）"""
    response = client.post(
        "/v1/books",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "直接添加的书籍",
            "authors": "",  # 空作者
            "publisher": None,
            "pub_date": None,
            "isbn": None
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "直接添加的书籍"
    assert data["authors"] == []  # 应该是空数组
    assert data["isbn13"].startswith("978")  # 应该生成978开头的唯一ISBN
    assert len(data["isbn13"]) == 13
    assert data["publisher"] is None
    assert data["pub_date"] is None


def test_create_book_without_isbn_creates_unique_records(client: TestClient, auth_token: str):
    """测试无ISBN创建书籍时，每本书生成唯一记录"""
    # 创建第一本书
    response1 = client.post(
        "/v1/books",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "书A",
            "authors": "",
            "publisher": None,
            "pub_date": None,
            "isbn": None
        }
    )
    assert response1.status_code == 200
    data1 = response1.json()

    # 创建第二本书
    response2 = client.post(
        "/v1/books",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "title": "书B",
            "authors": "",
            "publisher": None,
            "pub_date": None,
            "isbn": None
        }
    )
    assert response2.status_code == 200
    data2 = response2.json()

    # 两本书应该是不同的记录
    assert data1["id"] != data2["id"]
    assert data1["isbn13"] != data2["isbn13"]
    assert data1["title"] == "书A"
    assert data2["title"] == "书B"