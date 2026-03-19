from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import AuthUser, get_current_user
from app.db.database import get_session
from app.db.models import AcquiredType, BookCopy, BookMeta, Family

router = APIRouter(tags=["book_copies"])


def _require_family_owner(session: Session, family_id: int, user_id: int) -> Family:
    fam = session.exec(select(Family).where(Family.id == family_id)).first()
    if not fam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family not found")
    if fam.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not family owner")
    return fam


class BookCopyCreateRequest(BaseModel):
    book_meta_id: int
    acquired_type: AcquiredType = AcquiredType.other
    acquired_at: Optional[date] = None
    acquired_from: Optional[str] = None
    price_cny: Optional[float] = None
    note: Optional[str] = None


class BookCopyResponse(BaseModel):
    id: int
    family_id: int
    book_meta_id: int
    acquired_type: AcquiredType
    acquired_at: Optional[date] = None
    acquired_from: Optional[str] = None
    price_cny: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime


@router.post("/families/{family_id}/book_copies", response_model=BookCopyResponse)
def create_book_copy(
    family_id: int,
    req: BookCopyCreateRequest,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> BookCopyResponse:
    _require_family_owner(session, family_id, user.id)

    bm = session.exec(select(BookMeta).where(BookMeta.id == req.book_meta_id)).first()
    if not bm:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid book_meta_id")

    bc = BookCopy(
        family_id=family_id,
        book_meta_id=req.book_meta_id,
        acquired_type=req.acquired_type,
        acquired_at=req.acquired_at,
        acquired_from=req.acquired_from,
        price_cny=req.price_cny,
        note=req.note,
    )
    session.add(bc)
    session.commit()
    session.refresh(bc)
    return BookCopyResponse.model_validate(bc, from_attributes=True)


@router.get("/families/{family_id}/book_copies", response_model=list[BookCopyResponse])
def list_book_copies(
    family_id: int,
    book_meta_id: Optional[int] = None,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> list[BookCopyResponse]:
    _require_family_owner(session, family_id, user.id)
    stmt = select(BookCopy).where(BookCopy.family_id == family_id)
    if book_meta_id is not None:
        stmt = stmt.where(BookCopy.book_meta_id == book_meta_id)
    stmt = stmt.order_by(BookCopy.created_at.desc())
    rows = session.exec(stmt).all()
    return [BookCopyResponse.model_validate(r, from_attributes=True) for r in rows]

