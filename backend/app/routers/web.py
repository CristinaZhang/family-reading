"""Web frontend router — HTMX + Jinja2 pages served alongside the /v1 JSON API."""
from __future__ import annotations

import calendar
import csv
import io
import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer, BadSignature
from sqlmodel import Session, select

from app.auth import AuthUser
from app.db.database import get_session
from app.db.models import (
    BookMeta,
    Family,
    FamilyMember,
    ProgressType,
    Reading,
    ReadingStatus,
    User,
)
from app.utils.family_auth import require_family_owner

router = APIRouter()

# --- Auth helpers ---
_serializer = URLSafeSerializer("family-reading-web-secret", salt="web-session")
_COOKIE_NAME = "fr_session"
_STATUS_LABELS = {
    "wishlist": "想读",
    "reading": "在读",
    "finished": "读完",
    "paused": "搁置",
    "rereading": "重读",
}


def _set_session(response: Response, user_id: int) -> str:
    token = _serializer.dumps({"user_id": user_id})
    response.set_cookie(key=_COOKIE_NAME, value=token, httponly=True, samesite="lax")
    return f"u:{user_id}"


def _get_user_from_cookie(request: Request, session: Session) -> Optional[AuthUser]:
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        return None
    try:
        data = _serializer.loads(token)
    except BadSignature:
        return None
    user_id = data.get("user_id")
    if not user_id:
        return None
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        return None
    return AuthUser(id=user.id, openid=user.openid)


def _get_web_user_or_redirect(
    request: Request,
    session: Session,
) -> AuthUser | RedirectResponse:
    """Get web user from cookie or return a redirect to login."""
    user = _get_user_from_cookie(request, session)
    if not user:
        return RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)
    request.state.web_user = user
    return user


def require_web_user(
    request: Request,
    session: Session = Depends(get_session),
) -> AuthUser:
    """Raise HTTPException if not authenticated.

    For page routes that need a redirect instead, use _get_web_user_or_redirect() inline.
    """
    user = _get_user_from_cookie(request, session)
    if not user:
        raise HTTPException(status_code=401, detail="not authenticated")
    request.state.web_user = user
    return user


# --- Template setup ---
from jinja2 import Environment, FileSystemLoader

def _status_label(value: str) -> str:
    return _STATUS_LABELS.get(value, value)


_jinja_env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=True,
)
_jinja_env.globals["status_label"] = _status_label

templates = Jinja2Templates(env=_jinja_env)


def _template_response(request: Request, name: str, context: dict | None = None, **kwargs):
    """Wrapper for Starlette 1.0+ TemplateResponse (request is first arg, not in context)."""
    if context is None:
        context = {}
    context["request"] = request
    return templates.TemplateResponse(request=request, name=name, context=context, **kwargs)


# --- Page routes ---

@router.get("/web/login")
def login_page(request: Request) -> HTMLResponse:
    return _template_response(request, "login.html")


@router.post("/web/login")
def login_submit(
    request: Request,
    openid: str = Form(default=""),
    session: Session = Depends(get_session),
) -> Response:
    openid = openid.strip()
    if not openid:
        return _template_response(request, "login.html", {"error": "请输入 openid"})
    user = session.exec(select(User).where(User.openid == openid)).first()
    if not user:
        return _template_response(request, "login.html", {"error": "用户不存在，请确认 ENABLE_DEV_LOGIN=1"})
    response = RedirectResponse(url="/web/", status_code=status.HTTP_302_FOUND)
    _set_session(response, user.id)
    return response


@router.get("/web/logout")
def logout() -> Response:
    response = RedirectResponse(url="/web/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=_COOKIE_NAME)
    return response


@router.get("/web/")
def web_root(
    request: Request,
    session: Session = Depends(get_session),
) -> Response:
    user = _get_user_from_cookie(request, session)
    if not user:
        return RedirectResponse(url="/web/login")
    families = session.exec(select(Family).where(Family.owner_user_id == user.id)).all()
    if not families:
        return _template_response(request, "no_family.html")
    return RedirectResponse(url=f"/web/families/{families[0].id}/dashboard")


@router.post("/web/families")
def create_family_htmx(
    request: Request,
    name: str = Form(default="我家"),
    session: Session = Depends(get_session),
) -> Response:
    user = _get_user_from_cookie(request, session)
    if not user:
        return RedirectResponse(url="/web/login")
    name = name.strip() or "我家"
    fam = Family(name=name, owner_user_id=user.id)
    session.add(fam)
    session.commit()
    session.refresh(fam)
    # Auto-create a default member "我"
    session.add(FamilyMember(family_id=fam.id, display_name="我"))
    session.commit()
    return RedirectResponse(url=f"/web/families/{fam.id}/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/web/families/{family_id}/dashboard")
def dashboard_page(
    request: Request,
    family_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    members = session.exec(select(FamilyMember).where(FamilyMember.family_id == family_id)).all()
    rows = session.exec(select(Reading).where(Reading.family_id == family_id)).all()

    member_map = {m.id: m for m in members}
    counts: dict[int, dict[str, int]] = {}
    for m in members:
        counts[m.id] = {"wishlist": 0, "reading": 0, "finished": 0, "paused": 0, "rereading": 0}
    for r in rows:
        if r.member_id in counts:
            counts[r.member_id][r.status.value] += 1

    # Recent finished
    finished = sorted(
        [r for r in rows if r.status == ReadingStatus.finished],
        key=lambda r: r.finished_on or r.updated_at,
        reverse=True,
    )[:20]

    book_cache: dict[int, BookMeta] = {}
    for r in finished:
        if r.book_meta_id not in book_cache:
            bm = session.exec(select(BookMeta).where(BookMeta.id == r.book_meta_id)).first()
            if bm:
                book_cache[bm.id] = bm

    # Chart data
    status_totals = {"wishlist": 0, "reading": 0, "finished": 0, "paused": 0, "rereading": 0}
    for c in counts.values():
        for k in status_totals:
            status_totals[k] += c.get(k, 0)

    # Monthly trend (last 12 months)
    monthly_data: dict[str, int] = {}
    for r in rows:
        if r.status == ReadingStatus.finished and r.finished_on:
            key = r.finished_on.strftime("%Y-%m")
            monthly_data[key] = monthly_data.get(key, 0) + 1

    today = date.today()
    months: list[str] = []
    month_counts: list[int] = []
    for i in range(11, -1, -1):
        y = today.year - ((today.month - i - 1) // 12)
        m = ((today.month - i - 1) % 12) + 1
        key = f"{y}-{m:02d}"
        months.append(key)
        month_counts.append(monthly_data.get(key, 0))

    member_names = [m.display_name for m in members]
    member_finished = [counts[m.id]["finished"] for m in members]

    return _template_response(
        request,
        "dashboard.html",
        {
            "request": request,
            "family_id": family_id,
            "members": members,
            "member_map": member_map,
            "member_counts": counts,
            "recent_finished": finished,
            "book_cache": book_cache,
            "status_totals": status_totals,
            "chart_months": months,
            "chart_month_counts": month_counts,
            "member_names": member_names,
            "member_finished": member_finished,
        },
    )


@router.get("/web/families/{family_id}/readings")
def readings_page(
    request: Request,
    family_id: int,
    member_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    stmt = select(Reading).where(Reading.family_id == family_id)
    if member_id is not None:
        stmt = stmt.where(Reading.member_id == member_id)
    if status_filter:
        try:
            stmt = stmt.where(Reading.status == ReadingStatus(status_filter))
        except ValueError:
            pass
    stmt = stmt.order_by(Reading.updated_at.desc())
    readings = session.exec(stmt).all()

    members = session.exec(select(FamilyMember).where(FamilyMember.family_id == family_id)).all()
    member_map = {m.id: m for m in members}
    book_ids = {r.book_meta_id for r in readings}
    books = session.exec(select(BookMeta).where(BookMeta.id.in_(book_ids))).all()  # type: ignore[arg-type]
    book_map = {b.id: b for b in books}

    return _template_response(
        request,
        "readings.html",
        {
            "request": request,
            "family_id": family_id,
            "readings": readings,
            "members": members,
            "member_map": member_map,
            "book_map": book_map,
            "selected_member": member_id,
            "selected_status": status_filter,
            "statuses": [s.value for s in ReadingStatus],
        },
    )


@router.post("/web/families/{family_id}/readings")
def create_reading_htmx(
    request: Request,
    family_id: int,
    member_id: int = Form(),
    book_meta_id: int = Form(),
    reading_status: str = Form(default="reading"),
    started_on: Optional[str] = Form(default=None),
    note: Optional[str] = Form(default=None),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    rs = ReadingStatus(reading_status) if reading_status else ReadingStatus.reading
    r = Reading(
        family_id=family_id,
        member_id=member_id,
        book_meta_id=book_meta_id,
        status=rs,
        started_on=date.fromisoformat(started_on) if started_on else None,
        note=note,
    )
    session.add(r)
    session.commit()
    session.refresh(r)

    return RedirectResponse(url=f"/web/families/{family_id}/readings", status_code=status.HTTP_302_FOUND)


@router.patch("/web/families/{family_id}/readings/{reading_id}")
def patch_reading_htmx(
    request: Request,
    family_id: int,
    reading_id: int,
    status_val: Optional[str] = Form(default=None),
    progress_value: Optional[int] = Form(default=None),
    finished_on: Optional[str] = Form(default=None),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    r = session.exec(select(Reading).where(Reading.id == reading_id)).first()
    if not r:
        raise HTTPException(status_code=404, detail="not found")

    if status_val:
        r.status = ReadingStatus(status_val)
    if progress_value is not None:
        r.progress_value = progress_value
    if finished_on:
        r.finished_on = date.fromisoformat(finished_on)

    r.updated_at = datetime.utcnow()
    session.add(r)
    session.commit()

    return RedirectResponse(url=f"/web/families/{family_id}/readings", status_code=status.HTTP_302_FOUND)


@router.delete("/web/families/{family_id}/readings/{reading_id}")
def delete_reading_htmx(
    request: Request,
    family_id: int,
    reading_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    r = session.exec(select(Reading).where(Reading.id == reading_id)).first()
    if not r:
        raise HTTPException(status_code=404, detail="not found")
    session.delete(r)
    session.commit()

    return RedirectResponse(url=f"/web/families/{family_id}/readings", status_code=status.HTTP_302_FOUND)


@router.get("/web/families/{family_id}/books")
def books_page(
    request: Request,
    family_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    books = session.exec(select(BookMeta).order_by(BookMeta.created_at.desc())).all()
    members = session.exec(select(FamilyMember).where(FamilyMember.family_id == family_id)).all()

    return _template_response(
        request,
        "books.html",
        {
            "request": request,
            "family_id": family_id,
            "books": books,
            "members": members,
        },
    )


@router.post("/web/families/{family_id}/books")
def create_book_htmx(
    request: Request,
    family_id: int,
    title: str = Form(),
    authors: str = Form(default=""),
    isbn: Optional[str] = Form(default=None),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    author_list = [a.strip() for a in authors.split(",") if a.strip()] if authors else ["未知"]
    bm = BookMeta(
        title=title,
        authors_json=json.dumps(author_list, ensure_ascii=False),
        isbn13=isbn,
    )
    session.add(bm)
    session.commit()
    session.refresh(bm)

    return RedirectResponse(url=f"/web/families/{family_id}/books", status_code=status.HTTP_302_FOUND)


@router.delete("/web/families/{family_id}/books/{book_id}")
def delete_book_htmx(
    request: Request,
    family_id: int,
    book_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    bm = session.exec(select(BookMeta).where(BookMeta.id == book_id)).first()
    if not bm:
        raise HTTPException(status_code=404, detail="not found")
    session.delete(bm)
    session.commit()

    return RedirectResponse(url=f"/web/families/{family_id}/books", status_code=status.HTTP_302_FOUND)


@router.get("/web/families/{family_id}/members")
def members_page(
    request: Request,
    family_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    members = session.exec(select(FamilyMember).where(FamilyMember.family_id == family_id)).all()

    return _template_response(
        request,
        "members.html",
        {
            "request": request,
            "family_id": family_id,
            "members": members,
        },
    )


@router.post("/web/families/{family_id}/members")
def create_member_htmx(
    request: Request,
    family_id: int,
    display_name: str = Form(),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    display_name = display_name.strip()
    if not display_name:
        return RedirectResponse(url=f"/web/families/{family_id}/members", status_code=status.HTTP_302_FOUND)

    m = FamilyMember(family_id=family_id, display_name=display_name)
    session.add(m)
    session.commit()
    session.refresh(m)

    return RedirectResponse(url=f"/web/families/{family_id}/members", status_code=status.HTTP_302_FOUND)


# --- Export endpoints ---

@router.get("/web/families/{family_id}/export/readings.csv")
def export_readings_csv(
    request: Request,
    family_id: int,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    readings = session.exec(
        select(Reading).where(Reading.family_id == family_id).order_by(Reading.updated_at.desc())
    ).all()

    members = session.exec(select(FamilyMember).where(FamilyMember.family_id == family_id)).all()
    member_map = {m.id: m.display_name for m in members}

    book_ids = {r.book_meta_id for r in readings}
    books = session.exec(select(BookMeta).where(BookMeta.id.in_(book_ids))).all()  # type: ignore[arg-type]
    book_map = {b.id: b.title for b in books}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["成员", "书名", "状态", "开始日期", "结束日期", "进度", "备注", "更新时间"])
    for r in readings:
        progress_label = f"{r.progress_value}{'页' if r.progress_type == ProgressType.page else '%'}"
        writer.writerow([
            member_map.get(r.member_id, ""),
            book_map.get(r.book_meta_id, ""),
            r.status.value,
            str(r.started_on or ""),
            str(r.finished_on or ""),
            progress_label,
            r.note or "",
            str(r.updated_at.date()),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=readings_{family_id}.csv"},
    )


@router.get("/web/families/{family_id}/export/books.csv")
def export_books_csv(
    request: Request,
    family_id: int,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    user = require_web_user(request, session)
    require_family_owner(session, family_id, user.id)

    books = session.exec(select(BookMeta).order_by(BookMeta.created_at.desc())).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ISBN", "书名", "作者", "出版社", "出版日期", "添加时间"])
    for b in books:
        authors = ", ".join(json.loads(b.authors_json or "[]"))
        writer.writerow([
            b.isbn13 or "",
            b.title,
            authors,
            b.publisher or "",
            b.pub_date or "",
            str(b.created_at.date()),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=books_{family_id}.csv"},
    )
