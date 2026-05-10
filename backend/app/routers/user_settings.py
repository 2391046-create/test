"""
사용자 설정 관리 라우터 (통화, 국가, 예산 등)
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict

from app.database import get_db
from app.models.user import User
from app.models.transaction import BudgetSetting

router = APIRouter(prefix="/api/settings", tags=["settings"])


class UserSettingsUpdate(BaseModel):
    """사용자 설정 업데이트"""
    default_currency: Optional[str] = None
    country: Optional[str] = None


class BudgetSettingUpdate(BaseModel):
    """예산 설정 업데이트"""
    monthly_budget: float
    currency: str
    category_budgets: Optional[Dict[str, float]] = None


class UserSettingsResponse(BaseModel):
    """사용자 설정 응답"""
    user_id: str
    name: str
    email: str
    default_currency: str
    country: Optional[str]


@router.get("/user")
async def get_user_settings(
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 설정 조회
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "settings": {
                "user_id": str(user.id),
                "name": user.name,
                "email": user.email,
                "default_currency": user.default_currency,
                "country": user.country,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/user")
async def update_user_settings(
    body: UserSettingsUpdate,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자 설정 업데이트 (통화, 국가 등)
    """
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if body.default_currency:
            user.default_currency = body.default_currency.upper()
        
        if body.country:
            user.country = body.country
        
        await db.commit()
        await db.refresh(user)
        
        return {
            "success": True,
            "settings": {
                "user_id": str(user.id),
                "name": user.name,
                "email": user.email,
                "default_currency": user.default_currency,
                "country": user.country,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget")
async def get_budget_settings(
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    예산 설정 조회
    """
    try:
        result = await db.execute(
            select(BudgetSetting).where(BudgetSetting.user_id == user_id)
        )
        budget = result.scalar_one_or_none()
        
        if not budget:
            return {
                "success": True,
                "budget": None,
                "message": "No budget settings found"
            }
        
        return {
            "success": True,
            "budget": {
                "monthly_budget": float(budget.monthly_budget),
                "currency": budget.currency,
                "category_budgets": budget.category_budgets or {},
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/budget")
async def update_budget_settings(
    body: BudgetSettingUpdate,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    예산 설정 업데이트
    """
    try:
        # 기존 설정 조회
        result = await db.execute(
            select(BudgetSetting).where(BudgetSetting.user_id == user_id)
        )
        budget = result.scalar_one_or_none()
        
        if budget:
            # 기존 설정 업데이트
            budget.monthly_budget = body.monthly_budget
            budget.currency = body.currency
            budget.category_budgets = body.category_budgets or {}
        else:
            # 새 설정 생성
            budget = BudgetSetting(
                user_id=user_id,
                monthly_budget=body.monthly_budget,
                currency=body.currency,
                category_budgets=body.category_budgets or {},
            )
            db.add(budget)
        
        await db.commit()
        await db.refresh(budget)
        
        return {
            "success": True,
            "budget": {
                "monthly_budget": float(budget.monthly_budget),
                "currency": budget.currency,
                "category_budgets": budget.category_budgets or {},
            }
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-rates")
async def get_exchange_rates(
    base_currency: str = Query("USD"),
):
    """
    실시간 환율 조회
    """
    try:
        from app.services import exchange_rate_service
        
        rates = await exchange_rate_service.get_exchange_rates(base_currency)
        
        return {
            "success": True,
            "base_currency": base_currency,
            "rates": rates,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
