from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import User


@dataclass(frozen=True)
class AuthUser:
    id: int
    openid: str


def _parse_token(token: str) -> Optional[int]:
    # MVP token format: "u:<user_id>"
    if not token:
        return None
    if not token.startswith("u:"):
        return None
    try:
        return int(token[2:])
    except ValueError:
        return None


def get_current_user(
    session: Session = Depends(get_session),
    authorization: Optional[str] = Header(default=None),
) -> AuthUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    user_id = _parse_token(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return AuthUser(id=user.id, openid=user.openid)

