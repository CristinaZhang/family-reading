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
from app.services.book_provider import PlaceholderProvider, dumps_raw
from app.services.isbn import to_isbn13

router = APIRouter(tags=["books"])


class ResolveRequest(BaseModel):
    isbn: str


class BookMetaResponse(BaseModel):
    id: int
    isbn13: str
    title: str
    authors: list[str]
    publisher: Optional[str] = None
    pub_date: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    categories: list[str]
    created_at: datetime


_provider = PlaceholderProvider()


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

