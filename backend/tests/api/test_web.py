from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.db.models import (
    BookMeta,
    Family,
    FamilyMember,
    ProgressType,
    Reading,
    ReadingStatus,
    User,
)


@pytest.fixture
def test_user(test_db):
    """Create a test user and return it."""
    user = User(id=1, openid="test_user")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_family(test_db, test_user):
    """Create a test family owned by test_user."""
    family = Family(id=1, name="测试家庭", owner_user_id=test_user.id)
    test_db.add(family)
    test_db.commit()
    test_db.refresh(family)
    return family


@pytest.fixture
def test_member(test_db, test_family):
    """Create a test family member."""
    member = FamilyMember(id=1, family_id=test_family.id, display_name="小明")
    test_db.add(member)
    test_db.commit()
    test_db.refresh(member)
    return member


@pytest.fixture
def test_book(test_db):
    """Create a test book."""
    book = BookMeta(id=1, title="测试书籍", authors_json='["作者A"]')
    test_db.add(book)
    test_db.commit()
    test_db.refresh(book)
    return book


@pytest.fixture
def test_reading(test_db, test_family, test_member, test_book):
    """Create a test reading record."""
    reading = Reading(
        id=1,
        family_id=test_family.id,
        member_id=test_member.id,
        book_meta_id=test_book.id,
        status=ReadingStatus.reading,
        progress_type=ProgressType.page,
        progress_value=50,
    )
    test_db.add(reading)
    test_db.commit()
    test_db.refresh(reading)
    return reading


@pytest.fixture
def logged_in_client(client, test_user):
    """Get a client with valid web session cookie."""
    from itsdangerous import URLSafeSerializer
    serializer = URLSafeSerializer("family-reading-web-secret", salt="web-session")
    token = serializer.dumps({"user_id": test_user.id})
    client.cookies.set("fr_session", token)
    return client


def _is_redirect(status_code: int) -> bool:
    """Check if status code is a redirect (302 or 307)."""
    return status_code in (302, 307)


# --- Login tests ---

def test_login_page(client):
    """GET /web/login returns login page."""
    resp = client.get("/web/login")
    assert resp.status_code == 200
    assert "openid" in resp.text


def test_login_empty_openid(client, test_user):
    """POST /web/login with empty openid shows error."""
    resp = client.post("/web/login", data={"openid": ""}, follow_redirects=False)
    assert resp.status_code == 200
    assert "请输入 openid" in resp.text


def test_login_invalid_openid(client):
    """POST /web/login with non-existent openid shows error."""
    resp = client.post("/web/login", data={"openid": "nonexistent"}, follow_redirects=False)
    assert resp.status_code == 200
    assert "用户不存在" in resp.text


def test_login_success(client, test_user):
    """POST /web/login with valid openid sets cookie and redirects."""
    resp = client.post("/web/login", data={"openid": "test_user"}, follow_redirects=False)
    assert _is_redirect(resp.status_code)
    assert resp.headers["location"] == "/web/"
    assert "fr_session" in resp.cookies


# --- Session tests ---

def test_root_redirects_without_session(client):
    """GET /web/ redirects to login when no session."""
    resp = client.get("/web/", follow_redirects=False)
    assert _is_redirect(resp.status_code)
    assert resp.headers["location"] == "/web/login"


def test_root_redirects_to_dashboard(logged_in_client, test_family):
    """GET /web/ redirects to first family's dashboard when logged in."""
    resp = logged_in_client.get("/web/", follow_redirects=False)
    assert _is_redirect(resp.status_code)
    assert f"/web/families/{test_family.id}/dashboard" in resp.headers["location"]


def test_root_no_family(logged_in_client):
    """GET /web/ shows no_family page when user has no family."""
    resp = logged_in_client.get("/web/", follow_redirects=False)
    assert resp.status_code == 200
    assert "还没有家庭" in resp.text


def test_logout(logged_in_client):
    """GET /web/logout clears cookie and redirects to login."""
    resp = logged_in_client.get("/web/logout", follow_redirects=False)
    assert _is_redirect(resp.status_code)
    assert resp.headers["location"] == "/web/login"


def test_create_family_from_no_family_page(logged_in_client):
    """POST /web/families creates a family + default member and redirects to dashboard."""
    resp = logged_in_client.post(
        "/web/families",
        data={"name": "测试家庭"},
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)
    assert "/dashboard" in resp.headers["location"]


def test_create_family_default_name(logged_in_client):
    """POST /web/families with empty name uses default '我家'."""
    resp = logged_in_client.post(
        "/web/families",
        data={"name": ""},
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)


# --- Dashboard tests ---

def test_dashboard_page(logged_in_client, test_family, test_member):
    """GET /web/families/{id}/dashboard renders correctly."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/dashboard")
    assert resp.status_code == 200
    assert "阅读看板" in resp.text
    assert test_member.display_name in resp.text


def test_dashboard_unauthorized(client, test_family):
    """GET dashboard without session redirects to login."""
    resp = client.get(f"/web/families/{test_family.id}/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/web/login"


def test_dashboard_chart_data(logged_in_client, test_family, test_member):
    """Dashboard contains chart initialization data."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/dashboard")
    assert resp.status_code == 200
    assert "statusPie" in resp.text
    assert "monthlyLine" in resp.text
    assert "memberBar" in resp.text


# --- Readings tests ---

def test_readings_page_empty(logged_in_client, test_family):
    """GET readings page with no readings."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/readings")
    assert resp.status_code == 200
    assert "暂无阅读记录" in resp.text


def test_readings_page_with_data(logged_in_client, test_family, test_reading, test_member, test_book):
    """GET readings page shows existing readings."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/readings")
    assert resp.status_code == 200
    assert test_book.title in resp.text
    assert test_member.display_name in resp.text


def test_create_reading(logged_in_client, test_family, test_member, test_book):
    """POST creates a new reading and redirects."""
    resp = logged_in_client.post(
        f"/web/families/{test_family.id}/readings",
        data={
            "member_id": test_member.id,
            "book_meta_id": test_book.id,
            "reading_status": "reading",
        },
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)
    assert resp.headers["location"] == f"/web/families/{test_family.id}/readings"


def test_delete_reading(logged_in_client, test_family, test_reading):
    """DELETE removes a reading and redirects."""
    resp = logged_in_client.delete(
        f"/web/families/{test_family.id}/readings/{test_reading.id}",
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)


def test_patch_reading(logged_in_client, test_reading, test_family):
    """PATCH updates reading status."""
    resp = logged_in_client.patch(
        f"/web/families/{test_family.id}/readings/{test_reading.id}",
        data={"status_val": "finished"},
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)


# --- Books tests ---

def test_books_page_empty(logged_in_client, test_family):
    """GET books page with no books."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/books")
    assert resp.status_code == 200
    assert "暂无书籍" in resp.text


def test_books_page_with_data(logged_in_client, test_family, test_book):
    """GET books page shows existing books."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/books")
    assert resp.status_code == 200
    assert test_book.title in resp.text


def test_create_book(logged_in_client, test_family):
    """POST creates a new book and redirects."""
    resp = logged_in_client.post(
        f"/web/families/{test_family.id}/books",
        data={
            "title": "新书",
            "authors": "新作者",
        },
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)
    assert resp.headers["location"] == f"/web/families/{test_family.id}/books"


def test_delete_book(logged_in_client, test_family, test_book):
    """DELETE removes a book and redirects."""
    resp = logged_in_client.delete(
        f"/web/families/{test_family.id}/books/{test_book.id}",
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)


# --- Members tests ---

def test_members_page(logged_in_client, test_family, test_member):
    """GET members page shows existing members."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/members")
    assert resp.status_code == 200
    assert test_member.display_name in resp.text


def test_create_member(logged_in_client, test_family):
    """POST creates a new member and redirects."""
    resp = logged_in_client.post(
        f"/web/families/{test_family.id}/members",
        data={"display_name": "新成员"},
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)
    assert resp.headers["location"] == f"/web/families/{test_family.id}/members"


def test_create_member_empty_name(logged_in_client, test_family):
    """POST with empty name returns 422 (display_name is a required Form field)."""
    resp = logged_in_client.post(
        f"/web/families/{test_family.id}/members",
        data={"display_name": ""},
        follow_redirects=False,
    )
    assert resp.status_code == 422


def test_delete_member(logged_in_client, test_family, test_member):
    """DELETE removes a member and redirects."""
    resp = logged_in_client.delete(
        f"/web/families/{test_family.id}/members/{test_member.id}",
        follow_redirects=False,
    )
    assert _is_redirect(resp.status_code)


# --- Export tests ---

def test_export_readings_csv(logged_in_client, test_family, test_reading, test_member, test_book):
    """GET export/readings.csv returns CSV content."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/export/readings.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "成员" in resp.text
    assert "书名" in resp.text
    assert test_book.title in resp.text


def test_export_books_csv(logged_in_client, test_family, test_book):
    """GET export/books.csv returns CSV content."""
    resp = logged_in_client.get(f"/web/families/{test_family.id}/export/books.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "书名" in resp.text
    assert test_book.title in resp.text


# --- Readings filter tests ---

def test_readings_filter_by_status(logged_in_client, test_family, test_reading, test_member, test_book):
    """GET readings with status_filter only shows matching readings."""
    resp = logged_in_client.get(
        f"/web/families/{test_family.id}/readings?status_filter=reading"
    )
    assert resp.status_code == 200
    assert test_book.title in resp.text

    resp2 = logged_in_client.get(
        f"/web/families/{test_family.id}/readings?status_filter=finished"
    )
    assert resp2.status_code == 200
    assert "暂无阅读记录" in resp2.text
