from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import AuthUser, get_current_user
from app.db.database import get_session
from app.db.models import Family, FamilyMember

router = APIRouter(tags=["families"])


class FamilyCreateRequest(BaseModel):
    name: str


class FamilyResponse(BaseModel):
    id: int
    name: str
    owner_user_id: int
    created_at: datetime


@router.post("/families", response_model=FamilyResponse)
def create_family(
    req: FamilyCreateRequest,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> FamilyResponse:
    name = (req.name or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name required")
    fam = Family(name=name, owner_user_id=user.id)
    session.add(fam)
    session.commit()
    session.refresh(fam)
    return FamilyResponse.model_validate(fam, from_attributes=True)


@router.get("/families", response_model=list[FamilyResponse])
def list_families(
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> list[FamilyResponse]:
    # MVP：仅列出当前用户作为 owner 的家庭
    rows = session.exec(select(Family).where(Family.owner_user_id == user.id)).all()
    return [FamilyResponse.model_validate(r, from_attributes=True) for r in rows]


class MemberCreateRequest(BaseModel):
    display_name: str
    avatar_url: Optional[str] = None
    bound_user_id: Optional[int] = None


class MemberResponse(BaseModel):
    id: int
    family_id: int
    display_name: str
    avatar_url: Optional[str] = None
    bound_user_id: Optional[int] = None
    created_at: datetime


def _require_family_owner(session: Session, family_id: int, user_id: int) -> Family:
    fam = session.exec(select(Family).where(Family.id == family_id)).first()
    if not fam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family not found")
    if fam.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not family owner")
    return fam


@router.post("/families/{family_id}/members", response_model=MemberResponse)
def create_member(
    family_id: int,
    req: MemberCreateRequest,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> MemberResponse:
    _require_family_owner(session, family_id, user.id)
    display_name = (req.display_name or "").strip()
    if not display_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="display_name required")
    m = FamilyMember(
        family_id=family_id,
        display_name=display_name,
        avatar_url=req.avatar_url,
        bound_user_id=req.bound_user_id,
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return MemberResponse.model_validate(m, from_attributes=True)


@router.get("/families/{family_id}/members", response_model=list[MemberResponse])
def list_members(
    family_id: int,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> list[MemberResponse]:
    _require_family_owner(session, family_id, user.id)
    rows = session.exec(select(FamilyMember).where(FamilyMember.family_id == family_id)).all()
    return [MemberResponse.model_validate(r, from_attributes=True) for r in rows]

