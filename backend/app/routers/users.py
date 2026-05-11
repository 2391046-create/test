"""
사용자 관리 + 설정 라우터
"""
import uuid
import json
from datetime import datetime
from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.exchange_rate_service import get_all_rates_to_krw

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreateRequest(BaseModel):
    email: str
    name: Optional[str] = None
    default_currency: str = "USD"
    preferred_country: str = "USA"


class UserSettingsRequest(BaseModel):
    default_currency: Optional[str] = None
    preferred_country: Optional[str] = None
    monthly_budget: Optional[float] = None
    budget_currency: Optional[str] = None
    category_budgets: Optional[Dict[str, float]] = None


def _user_to_dict(u: User) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "name": u.name,
        "default_currency": u.default_currency,
        "preferred_country": u.preferred_country,
        "monthly_budget": u.monthly_budget,
        "budget_currency": u.budget_currency,
        "category_budgets": json.loads(u.category_budgets or "{}"),
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.post("/create")
async def create_user(body: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    """사용자 생성"""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 존재하는 이메일입니다")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        name=body.name,
        default_currency=body.default_currency,
        preferred_country=body.preferred_country,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"success": True, "user": _user_to_dict(user)}


@router.get("/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """사용자 조회"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return {"success": True, "user": _user_to_dict(user)}


@router.put("/{user_id}/settings")
async def update_settings(user_id: str, body: UserSettingsRequest, db: AsyncSession = Depends(get_db)):
    """
    사용자 설정 업데이트 (통화, 국가, 예산)
    - 이 설정이 모든 서비스에 실시간 반영됨
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    if body.default_currency:
        user.default_currency = body.default_currency
    if body.preferred_country:
        user.preferred_country = body.preferred_country
    if body.monthly_budget is not None:
        user.monthly_budget = body.monthly_budget
    if body.budget_currency:
        user.budget_currency = body.budget_currency
    if body.category_budgets is not None:
        user.category_budgets = json.dumps(body.category_budgets)

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return {"success": True, "user": _user_to_dict(user)}


@router.get("/{user_id}/settings")
async def get_settings(user_id: str, db: AsyncSession = Depends(get_db)):
    """사용자 설정 조회"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return {"success": True, "settings": _user_to_dict(user)}
