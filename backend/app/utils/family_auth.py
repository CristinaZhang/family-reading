"""Shared family ownership check, used by API routers and web router."""
from __future__ import annotations

from sqlmodel import Session, select

from app.db.models import Family


def require_family_owner(session: Session, family_id: int, user_id: int) -> Family:
    """Verify the user is the owner of the given family.

    Raises 404 if family not found, 403 if not the owner.
    """
    fam = session.exec(select(Family).where(Family.id == family_id)).first()
    if not fam:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="family not found")
    if fam.owner_user_id != user_id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not family owner")
    return fam
