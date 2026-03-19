from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from sqlmodel import Field, SQLModel


class NowMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class UpdatedMixin(SQLModel):
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    openid: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class Family(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    owner_user_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class FamilyMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(index=True)
    display_name: str
    avatar_url: Optional[str] = None
    bound_user_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class BookMeta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    isbn13: str = Field(index=True, unique=True)
    title: str
    authors_json: str = "[]"
    publisher: Optional[str] = None
    pub_date: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    categories_json: str = "[]"
    raw_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class AcquiredType(str, Enum):
    purchase = "purchase"
    gift = "gift"
    school = "school"
    library = "library"
    other = "other"


class BookCopy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(index=True)
    book_meta_id: int = Field(index=True)
    acquired_type: AcquiredType = Field(default=AcquiredType.other, index=True)
    acquired_at: Optional[date] = None
    acquired_from: Optional[str] = None
    price_cny: Optional[float] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class ReadingStatus(str, Enum):
    wishlist = "wishlist"
    reading = "reading"
    finished = "finished"
    paused = "paused"
    rereading = "rereading"


class ProgressType(str, Enum):
    page = "page"
    percent = "percent"


class Reading(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(index=True)
    member_id: int = Field(index=True)
    book_meta_id: int = Field(index=True)
    book_copy_id: Optional[int] = Field(default=None, index=True)

    status: ReadingStatus = Field(default=ReadingStatus.reading, index=True)
    started_on: Optional[date] = Field(default=None, index=True)
    finished_on: Optional[date] = Field(default=None, index=True)
    last_read_on: Optional[date] = Field(default=None, index=True)
    progress_type: ProgressType = Field(default=ProgressType.page, index=True)
    progress_value: int = 0
    note: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)


def utcnow() -> datetime:
    return datetime.utcnow()

