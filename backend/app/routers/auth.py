from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings
from app.db.database import get_session
from app.db.models import User

router = APIRouter(tags=["auth"])


class DevLoginRequest(BaseModel):
    openid: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/auth/dev/login", response_model=LoginResponse)
def dev_login(req: DevLoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    if not settings.enable_dev_login:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="dev login disabled")

    openid = (req.openid or "").strip()
    if not openid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="openid required")

    user = session.exec(select(User).where(User.openid == openid)).first()
    if not user:
        user = User(openid=openid)
        session.add(user)
        session.commit()
        session.refresh(user)

    token = f"u:{user.id}"
    return LoginResponse(access_token=token, user={"id": user.id, "openid": user.openid})


class WechatLoginRequest(BaseModel):
    code: str


@router.post("/auth/wechat/login", response_model=LoginResponse)
def wechat_login(_: WechatLoginRequest) -> LoginResponse:
    # MVP：不直接对接微信 code2session。
    # 生产环境可替换为：
    # 1) 通过微信接口将 code 换取 openid/session_key
    # 2) 创建/查询用户
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="wechat login not implemented in MVP; use /auth/dev/login",
    )

