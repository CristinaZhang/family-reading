from __future__ import annotations

import httpx
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


import logging

logger = logging.getLogger(__name__)

@router.post("/auth/wechat/login", response_model=LoginResponse)
async def wechat_login(req: WechatLoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    logger.info(f"Received WeChat login request with code: {req.code}")

    if not settings.wechat_app_id or not settings.wechat_app_secret:
        logger.error("WeChat app ID or secret not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="WeChat app ID or secret not configured",
        )

    code = (req.code or "").strip()
    if not code:
        logger.error("Code is required")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code required")

    # 调用微信 code2session API
    try:
        logger.info(f"Calling WeChat code2session API with code: {code}")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params={
                    "appid": settings.wechat_app_id,
                    "secret": settings.wechat_app_secret,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
                timeout=10.0,
            )
            logger.info(f"WeChat API response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            logger.info(f"WeChat API response data: {data}")

            # 检查是否有错误
            if "errcode" in data and data["errcode"] != 0:
                logger.error(f"WeChat API error: {data.get('errmsg', 'Unknown error')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"WeChat API error: {data.get('errmsg', 'Unknown error')}",
                )

            openid = data.get("openid")
            if not openid:
                logger.error("No openid returned from WeChat API")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No openid returned from WeChat API",
                )
            logger.info(f"Retrieved openid: {openid}")

    except httpx.HTTPError as e:
        logger.error(f"Failed to call WeChat API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to call WeChat API: {str(e)}",
        )

    # 创建或查询用户
    user = session.exec(select(User).where(User.openid == openid)).first()
    if not user:
        logger.info(f"Creating new user with openid: {openid}")
        user = User(openid=openid)
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        logger.info(f"User found with openid: {openid}, user id: {user.id}")

    # 生成令牌
    token = f"u:{user.id}"
    logger.info(f"Login successful for user id: {user.id}, token generated")
    return LoginResponse(access_token=token, user={"id": user.id, "openid": user.openid})