from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field as PydField
from sqlmodel import Session, select

from app.auth import AuthUser, get_current_user
from app.db.database import get_session
from app.db.models import BookCopy, BookMeta, Family, FamilyMember, ProgressType, Reading, ReadingStatus

router = APIRouter(tags=["readings"])


def _require_family_owner(session: Session, family_id: int, user_id: int) -> Family:
    fam = session.exec(select(Family).where(Family.id == family_id)).first()
    if not fam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family not found")
    if fam.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not family owner")
    return fam


class BookCopyCreate(BaseModel):
    acquired_type: str = "other"
    acquired_at: Optional[date] = None
    acquired_from: Optional[str] = None
    price_cny: Optional[float] = None
    note: Optional[str] = None


class ReadingCreateRequest(BaseModel):
    family_id: int
    member_id: int
    book_meta_id: int
    status: ReadingStatus = ReadingStatus.reading
    started_on: Optional[date] = None
    finished_on: Optional[date] = None
    last_read_on: Optional[date] = None
    progress_type: ProgressType = ProgressType.page
    progress_value: int = 0
    note: Optional[str] = None

    create_book_copy: Optional[BookCopyCreate] = None


class ReadingResponse(BaseModel):
    id: int
    family_id: int
    member_id: int
    book_meta_id: int
    book_copy_id: Optional[int] = None
    status: ReadingStatus
    started_on: Optional[date] = None
    finished_on: Optional[date] = None
    last_read_on: Optional[date] = None
    progress_type: ProgressType
    progress_value: int
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime


@router.post("/readings", response_model=ReadingResponse)
def create_reading(
    req: ReadingCreateRequest,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> ReadingResponse:
    _require_family_owner(session, req.family_id, user.id)

    member = session.exec(
        select(FamilyMember).where(FamilyMember.id == req.member_id, FamilyMember.family_id == req.family_id)
    ).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid member_id")

    book = session.exec(select(BookMeta).where(BookMeta.id == req.book_meta_id)).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid book_meta_id")

    book_copy_id: Optional[int] = None
    if req.create_book_copy is not None:
        bc = BookCopy(
            family_id=req.family_id,
            book_meta_id=req.book_meta_id,
            acquired_type=req.create_book_copy.acquired_type,  # validated by Enum coercion
            acquired_at=req.create_book_copy.acquired_at,
            acquired_from=req.create_book_copy.acquired_from,
            price_cny=req.create_book_copy.price_cny,
            note=req.create_book_copy.note,
        )
        session.add(bc)
        session.commit()
        session.refresh(bc)
        book_copy_id = bc.id

    r = Reading(
        family_id=req.family_id,
        member_id=req.member_id,
        book_meta_id=req.book_meta_id,
        book_copy_id=book_copy_id,
        status=req.status,
        started_on=req.started_on,
        finished_on=req.finished_on,
        last_read_on=req.last_read_on,
        progress_type=req.progress_type,
        progress_value=req.progress_value,
        note=req.note,
    )
    session.add(r)
    session.commit()
    session.refresh(r)

    return ReadingResponse.model_validate(r, from_attributes=True)


class ReadingPatchRequest(BaseModel):
    status: Optional[ReadingStatus] = None
    started_on: Optional[date] = None
    finished_on: Optional[date] = None
    last_read_on: Optional[date] = None
    progress_type: Optional[ProgressType] = None
    progress_value: Optional[int] = PydField(default=None, ge=0)
    note: Optional[str] = None


@router.patch("/readings/{reading_id}", response_model=ReadingResponse)
def patch_reading(
    reading_id: int,
    req: ReadingPatchRequest,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> ReadingResponse:
    r = session.exec(select(Reading).where(Reading.id == reading_id)).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="reading not found")
    _require_family_owner(session, r.family_id, user.id)

    if req.status is not None:
        r.status = req.status
    if req.progress_type is not None:
        r.progress_type = req.progress_type
    if req.progress_value is not None:
        r.progress_value = req.progress_value
    if req.started_on is not None:
        r.started_on = req.started_on
    if req.finished_on is not None:
        r.finished_on = req.finished_on
    if req.last_read_on is not None:
        r.last_read_on = req.last_read_on
    if req.note is not None:
        r.note = req.note

    r.updated_at = datetime.utcnow()
    session.add(r)
    session.commit()
    session.refresh(r)
    return ReadingResponse.model_validate(r, from_attributes=True)


@router.get("/families/{family_id}/readings", response_model=list[ReadingResponse])
def list_readings(
    family_id: int,
    member_id: Optional[int] = None,
    status_filter: Optional[ReadingStatus] = None,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> list[ReadingResponse]:
    _require_family_owner(session, family_id, user.id)

    stmt = select(Reading).where(Reading.family_id == family_id)
    if member_id is not None:
        stmt = stmt.where(Reading.member_id == member_id)
    if status_filter is not None:
        stmt = stmt.where(Reading.status == status_filter)
    stmt = stmt.order_by(Reading.updated_at.desc())

    rows = session.exec(stmt).all()
    return [ReadingResponse.model_validate(r, from_attributes=True) for r in rows]

