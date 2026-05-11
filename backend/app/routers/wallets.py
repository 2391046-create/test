"""
XRPL 지갑 관리 라우터
"""
import uuid
import base64
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.wallet import Wallet
from app.services import xrpl_service

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


class WalletConnectRequest(BaseModel):
    user_id: str
    wallet_seed: str
    wallet_name: Optional[str] = "My XRPL Wallet"


class WalletValidateRequest(BaseModel):
    wallet_seed: str


@router.post("/connect")
async def connect_wallet(body: WalletConnectRequest, db: AsyncSession = Depends(get_db)):
    """
    XRPL 지갑 연결
    - seed로 지갑 주소 추출
    - 암호화하여 DB 저장
    - 중복 연결 방지
    """
    # 지갑 검증
    validation = xrpl_service.validate_wallet(body.wallet_seed)
    if not validation["success"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    address = validation["address"]

    # 중복 확인
    existing = await db.execute(select(Wallet).where(Wallet.address == address))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 연결된 지갑입니다")

    # seed 암호화 저장 (base64 인코딩 - 실제 서비스에서는 더 강력한 암호화 사용)
    encoded_seed = base64.b64encode(body.wallet_seed.encode()).decode()

    wallet = Wallet(
        id=str(uuid.uuid4()),
        user_id=body.user_id,
        name=body.wallet_name,
        address=address,
        public_key=validation.get("public_key", ""),
        encrypted_seed=encoded_seed,
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)

    return {
        "success": True,
        "wallet": {
            "id": wallet.id,
            "address": wallet.address,
            "name": wallet.name,
            "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
        }
    }


@router.post("/validate")
async def validate_wallet(body: WalletValidateRequest):
    """지갑 seed 검증 (저장 안 함)"""
    result = xrpl_service.validate_wallet(body.wallet_seed)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "address": result["address"]}


@router.get("/list")
async def list_wallets(user_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    """사용자의 지갑 목록 조회"""
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id).where(Wallet.is_active == True)
    )
    wallets = result.scalars().all()

    return {
        "success": True,
        "wallets": [
            {
                "id": w.id,
                "address": w.address,
                "name": w.name,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in wallets
        ]
    }


@router.get("/{wallet_id}/balance")
async def get_balance(wallet_id: str, db: AsyncSession = Depends(get_db)):
    """XRPL 지갑 실시간 잔액 조회"""
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="지갑을 찾을 수 없습니다")

    balance = xrpl_service.get_account_balance(wallet.address)
    if not balance["success"]:
        # 잔액 조회 실패해도 지갑 정보는 반환
        return {
            "success": True,
            "wallet_id": wallet_id,
            "address": wallet.address,
            "balance_xrp": 0,
            "error": balance.get("error"),
        }

    return {
        "success": True,
        "wallet_id": wallet_id,
        "address": wallet.address,
        "balance_xrp": balance["balance_xrp"],
        "balance_drops": balance["balance_drops"],
    }


@router.delete("/{wallet_id}")
async def delete_wallet(wallet_id: str, db: AsyncSession = Depends(get_db)):
    """지갑 삭제"""
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="지갑을 찾을 수 없습니다")

    wallet.is_active = False
    await db.commit()
    return {"success": True, "message": "지갑이 삭제되었습니다"}
