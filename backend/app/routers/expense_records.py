"""지출 내역 XRPL 기록 및 더치페이 정산"""
import json
import uuid
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import XrplTransaction
from app.models.wallet import Wallet
from app.services import xrpl_service

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


class ExpenseItem(BaseModel):
    name: str
    quantity: int = 1
    price: float


class RecordExpenseRequest(BaseModel):
    """지출 내역을 XRPL에 기록"""

    wallet_id: Optional[uuid.UUID] = None
    wallet_seed: Optional[str] = None  # 직접 seed 제공
    merchant: str
    amount: float
    currency: str
    category: str = "receipt"  # receipt, menu, dutch_pay
    items: Optional[List[ExpenseItem]] = None
    description: Optional[str] = None
    num_people: int = 1  # 더치페이 인원


class DutchPayRequest(BaseModel):
    """더치페이 정산"""

    wallet_id: Optional[uuid.UUID] = None
    wallet_seed: Optional[str] = None
    merchant: str
    total_amount: float
    currency: str
    members: List[str]  # 참가자 이름
    items: Optional[List[ExpenseItem]] = None


class ExpenseResponse(BaseModel):
    success: bool
    tx_hash: Optional[str] = None
    memo_data: Optional[dict] = None
    error: Optional[str] = None


@router.post("/record", response_model=ExpenseResponse)
async def record_expense(body: RecordExpenseRequest, db: AsyncSession = Depends(get_db)):
    """지출 내역을 XRPL Memo에 기록"""
    try:
        # 지갑 정보 확인
        wallet = None
        seed = body.wallet_seed

        if body.wallet_id:
            result = await db.execute(select(Wallet).where(Wallet.id == body.wallet_id))
            wallet = result.scalar_one_or_none()
            if not wallet:
                return ExpenseResponse(success=False, error="Wallet not found")
            seed = xrpl_service.decrypt_seed(wallet.encrypted_seed)

        if not seed:
            return ExpenseResponse(success=False, error="wallet_seed is required")

        # 지출 정보 JSON 생성
        expense_data = {
            "merchant": body.merchant,
            "amount": body.amount,
            "currency": body.currency,
            "category": body.category,
            "description": body.description or "",
            "num_people": body.num_people,
            "items": [
                {"name": item.name, "quantity": item.quantity, "price": item.price}
                for item in (body.items or [])
            ],
        }

        # XRPL에 기록
        result = await xrpl_service.record_transaction_with_memo(seed, expense_data)

        if not result.get("success"):
            return ExpenseResponse(success=False, error=result.get("error", "Failed to record"))

        # DB에 저장
        if wallet:
            tx = XrplTransaction(
                wallet_id=wallet.id,
                tx_type="ExpenseRecord",
                xrpl_tx_hash=result["tx_hash"],
                status="success",
                amount=Decimal(body.amount),
                currency=body.currency,
                memo=json.dumps(expense_data),
            )
            db.add(tx)
            await db.commit()

        return ExpenseResponse(
            success=True,
            tx_hash=result["tx_hash"],
            memo_data=expense_data,
        )

    except Exception as e:
        return ExpenseResponse(success=False, error=str(e))


@router.post("/dutch-pay", response_model=ExpenseResponse)
async def record_dutch_pay(body: DutchPayRequest, db: AsyncSession = Depends(get_db)):
    """더치페이 정산을 XRPL에 기록"""
    try:
        # 지갑 정보 확인
        wallet = None
        seed = body.wallet_seed

        if body.wallet_id:
            result = await db.execute(select(Wallet).where(Wallet.id == body.wallet_id))
            wallet = result.scalar_one_or_none()
            if not wallet:
                return ExpenseResponse(success=False, error="Wallet not found")
            seed = xrpl_service.decrypt_seed(wallet.encrypted_seed)

        if not seed:
            return ExpenseResponse(success=False, error="wallet_seed is required")

        # 더치페이 정보 JSON 생성
        num_people = len(body.members)
        per_person = body.total_amount / num_people

        dutch_pay_data = {
            "type": "dutch_pay",
            "merchant": body.merchant,
            "total_amount": body.total_amount,
            "currency": body.currency,
            "num_people": num_people,
            "per_person": round(per_person, 2),
            "members": body.members,
            "items": [
                {"name": item.name, "quantity": item.quantity, "price": item.price}
                for item in (body.items or [])
            ],
        }

        # XRPL에 기록
        result = await xrpl_service.record_transaction_with_memo(seed, dutch_pay_data)

        if not result.get("success"):
            return ExpenseResponse(success=False, error=result.get("error", "Failed to record"))

        # DB에 저장
        if wallet:
            tx = XrplTransaction(
                wallet_id=wallet.id,
                tx_type="DutchPay",
                xrpl_tx_hash=result["tx_hash"],
                status="success",
                amount=Decimal(body.total_amount),
                currency=body.currency,
                memo=json.dumps(dutch_pay_data),
            )
            db.add(tx)
            await db.commit()

        return ExpenseResponse(
            success=True,
            tx_hash=result["tx_hash"],
            memo_data=dutch_pay_data,
        )

    except Exception as e:
        return ExpenseResponse(success=False, error=str(e))
