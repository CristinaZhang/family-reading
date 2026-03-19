from __future__ import annotations

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import AuthUser, get_current_user
from app.db.database import get_session
from app.db.models import Family, FamilyMember, Reading, ReadingStatus

router = APIRouter(tags=["dashboard"])


def _require_family_owner(session: Session, family_id: int, user_id: int) -> Family:
    fam = session.exec(select(Family).where(Family.id == family_id)).first()
    if not fam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family not found")
    if fam.owner_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not family owner")
    return fam


class MemberDashboard(BaseModel):
    member_id: int
    display_name: str
    wishlist: int
    reading: int
    finished: int
    paused: int
    rereading: int


class DashboardResponse(BaseModel):
    family_id: int
    members: list[MemberDashboard]


@router.get("/families/{family_id}/dashboard", response_model=DashboardResponse)
def dashboard(
    family_id: int,
    session: Session = Depends(get_session),
    user: AuthUser = Depends(get_current_user),
) -> DashboardResponse:
    _require_family_owner(session, family_id, user.id)

    members = session.exec(select(FamilyMember).where(FamilyMember.family_id == family_id)).all()
    member_map = {m.id: m for m in members}

    counts = defaultdict(lambda: defaultdict(int))
    rows = session.exec(select(Reading).where(Reading.family_id == family_id)).all()
    for r in rows:
        counts[r.member_id][r.status.value] += 1

    out: list[MemberDashboard] = []
    for mid, m in member_map.items():
        c = counts[mid]
        out.append(
            MemberDashboard(
                member_id=mid,
                display_name=m.display_name,
                wishlist=c.get(ReadingStatus.wishlist.value, 0),
                reading=c.get(ReadingStatus.reading.value, 0),
                finished=c.get(ReadingStatus.finished.value, 0),
                paused=c.get(ReadingStatus.paused.value, 0),
                rereading=c.get(ReadingStatus.rereading.value, 0),
            )
        )

    return DashboardResponse(family_id=family_id, members=out)

