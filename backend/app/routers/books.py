from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import AuthUser, get_current_user
from app.db.database import get_session
from app.db.models import BookMeta
from app.services.book_provider import RealBookProvider, dumps_raw
from app.services.isbn import to_isbn13

router = APIRouter(tags=["books"])


class ResolveRequest(BaseModel):
    isbn: str


class CreateBookRequest(BaseModel):
    title: str
    authors: str  # 逗号分隔的作者列表
    publisher: Optional[str] = None
    pub_date: Optional[str] = None
    isbn: Optional[str] = None


class BookMetaResponse(BaseModel):
    id: int
    isbn13: Optional[str] = None
    title: str
    authors: list[str]
    publisher: Optional[str] = None
    pub_date: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    categories: list[str]
    created_at: datetime


_provider = RealBookProvider()


@router.post("/books/resolve", response_model=BookMetaResponse)
def resolve_book(
    req: ResolveRequest,
    session: Session = Depends(get_session),
    _: AuthUser = Depends(get_current_user),
) -> BookMetaResponse:
    try:
        isbn13 = to_isbn13(req.isbn)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid isbn")

    existing = session.exec(select(BookMeta).where(BookMeta.isbn13 == isbn13)).first()
    if existing:
        return BookMetaResponse(
            id=existing.id,
            isbn13=existing.isbn13,
            title=existing.title,
            authors=json.loads(existing.authors_json or "[]"),
            publisher=existing.publisher,
            pub_date=existing.pub_date,
            cover_url=existing.cover_url,
            summary=existing.summary,
            categories=json.loads(existing.categories_json or "[]"),
            created_at=existing.created_at,
        )

    payload = _provider.resolve(isbn13)
    bm = BookMeta(
        isbn13=payload.isbn13,
        title=payload.title,
        authors_json=json.dumps(payload.authors or [], ensure_ascii=False),
        publisher=payload.publisher,
        pub_date=payload.pub_date,
        cover_url=payload.cover_url,
        summary=payload.summary,
        categories_json=json.dumps(payload.categories or [], ensure_ascii=False),
        raw_json=dumps_raw(payload.raw),
    )
    session.add(bm)
    session.commit()
    session.refresh(bm)

    return BookMetaResponse(
        id=bm.id,
        isbn13=bm.isbn13,
        title=bm.title,
        authors=payload.authors or [],
        publisher=bm.publisher,
        pub_date=bm.pub_date,
        cover_url=bm.cover_url,
        summary=bm.summary,
        categories=payload.categories or [],
        created_at=bm.created_at,
    )


@router.post("/books", response_model=BookMetaResponse)
def create_book(
    req: CreateBookRequest,
    session: Session = Depends(get_session),
    _: AuthUser = Depends(get_current_user),
) -> BookMetaResponse:
    # 处理ISBN
    isbn13 = None
    if req.isbn:
        try:
            isbn13 = to_isbn13(req.isbn)
        except ValueError:
            pass

    # 处理作者列表
    authors = [author.strip() for author in req.authors.split(",") if author.strip()]

    # 只在有真实ISBN时检查重复
    existing = None
    if isbn13 is not None:
        existing = session.exec(select(BookMeta).where(BookMeta.isbn13 == isbn13)).first()
    if existing:
        # 更新现有书籍
        existing.title = req.title
        existing.authors_json = json.dumps(authors, ensure_ascii=False)
        existing.publisher = req.publisher
        existing.pub_date = req.pub_date
        session.commit()
        session.refresh(existing)

        return BookMetaResponse(
            id=existing.id,
            isbn13=existing.isbn13,
            title=existing.title,
            authors=authors,
            publisher=existing.publisher,
            pub_date=existing.pub_date,
            cover_url=existing.cover_url,
            summary=existing.summary,
            categories=json.loads(existing.categories_json or "[]"),
            created_at=existing.created_at,
        )

    # 创建新书籍
    bm = BookMeta(
        isbn13=isbn13,
        title=req.title,
        authors_json=json.dumps(authors, ensure_ascii=False),
        publisher=req.publisher,
        pub_date=req.pub_date,
        cover_url=None,
        summary=None,
        categories_json=json.dumps([], ensure_ascii=False),
        raw_json=dumps_raw({"provider": "manual"}),
    )
    session.add(bm)
    session.commit()
    session.refresh(bm)

    return BookMetaResponse(
        id=bm.id,
        isbn13=bm.isbn13,
        title=bm.title,
        authors=authors,
        publisher=bm.publisher,
        pub_date=bm.pub_date,
        cover_url=bm.cover_url,
        summary=bm.summary,
        categories=[],
        created_at=bm.created_at,
    )


class PatchBookRequest(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    pub_date: Optional[str] = None


@router.get("/books", response_model=list[BookMetaResponse])
def list_books(
    session: Session = Depends(get_session),
    _: AuthUser = Depends(get_current_user),
) -> list[BookMetaResponse]:
    rows = session.exec(select(BookMeta).order_by(BookMeta.created_at.desc())).all()
    return [
        BookMetaResponse(
            id=b.id,
            isbn13=b.isbn13,
            title=b.title,
            authors=json.loads(b.authors_json or "[]"),
            publisher=b.publisher,
            pub_date=b.pub_date,
            cover_url=b.cover_url,
            summary=b.summary,
            categories=json.loads(b.categories_json or "[]"),
            created_at=b.created_at,
        )
        for b in rows
    ]


@router.patch("/books/{book_id}", response_model=BookMetaResponse)
def patch_book(
    book_id: int,
    req: PatchBookRequest,
    session: Session = Depends(get_session),
    _: AuthUser = Depends(get_current_user),
) -> BookMetaResponse:
    bm = session.exec(select(BookMeta).where(BookMeta.id == book_id)).first()
    if not bm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="book not found")

    if req.title is not None:
        bm.title = req.title
    if req.authors is not None:
        authors = [a.strip() for a in req.authors.split(",") if a.strip()]
        bm.authors_json = json.dumps(authors, ensure_ascii=False)
    if req.publisher is not None:
        bm.publisher = req.publisher
    if req.pub_date is not None:
        bm.pub_date = req.pub_date

    session.commit()
    session.refresh(bm)

    return BookMetaResponse(
        id=bm.id,
        isbn13=bm.isbn13,
        title=bm.title,
        authors=json.loads(bm.authors_json or "[]"),
        publisher=bm.publisher,
        pub_date=bm.pub_date,
        cover_url=bm.cover_url,
        summary=bm.summary,
        categories=json.loads(bm.categories_json or "[]"),
        created_at=bm.created_at,
    )


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    session: Session = Depends(get_session),
    _: AuthUser = Depends(get_current_user),
) -> None:
    bm = session.exec(select(BookMeta).where(BookMeta.id == book_id)).first()
    if not bm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="book not found")
    session.delete(bm)
    session.commit()