"""
지갑 연결 및 관리 라우터 (확장)
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.wallet import Wallet
from app.models.user import User
from app.services import xrpl_service

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


class WalletConnectRequest(BaseModel):
    """지갑 연결 요청"""
    wallet_seed: str
    wallet_name: Optional[str] = None


class WalletResponse(BaseModel):
    """지갑 응답"""
    id: str
    user_id: str
    wallet_name: str
    xrpl_address: str
    created_at: str


class WalletBalanceResponse(BaseModel):
    """지갑 잔액 응답"""
    address: str
    balances: dict  # {"XRP": 100, "USD": 500, ...}


@router.post("/connect")
async def connect_wallet(
    body: WalletConnectRequest,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자가 XRPL 지갑을 연결
    """
    try:
        # 사용자 확인
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 지갑 주소 추출
        try:
            wallet_address = xrpl_service.get_address_from_seed(body.wallet_seed)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid wallet seed: {str(e)}")
        
        # 기존 지갑 확인
        existing = await db.execute(
            select(Wallet).where(
                Wallet.xrpl_address == wallet_address
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Wallet already connected")
        
        # 새 지갑 생성
        wallet = Wallet(
            user_id=user_id,
            wallet_name=body.wallet_name or f"Wallet {wallet_address[:8]}",
            xrpl_address=wallet_address,
            encrypted_seed=xrpl_service.encrypt_seed(body.wallet_seed),
        )
        
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        
        return {
            "success": True,
            "wallet": {
                "id": str(wallet.id),
                "wallet_name": wallet.wallet_name,
                "xrpl_address": wallet.xrpl_address,
                "created_at": wallet.created_at.isoformat(),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_wallets(
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    사용자의 모든 지갑 조회
    """
    try:
        result = await db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallets = result.scalars().all()
        
        return {
            "success": True,
            "wallets": [
                {
                    "id": str(w.id),
                    "wallet_name": w.wallet_name,
                    "xrpl_address": w.xrpl_address,
                    "created_at": w.created_at.isoformat(),
                }
                for w in wallets
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{wallet_id}/balance")
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    지갑 잔액 조회
    """
    try:
        # 지갑 조회
        result = await db.execute(
            select(Wallet).where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id,
            )
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # XRPL에서 잔액 조회
        balance_info = await xrpl_service.get_account_balance(wallet.xrpl_address)
        
        return {
            "success": True,
            "address": wallet.xrpl_address,
            "balances": balance_info,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{wallet_id}")
async def delete_wallet(
    wallet_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    지갑 삭제
    """
    try:
        result = await db.execute(
            select(Wallet).where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id,
            )
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        await db.delete(wallet)
        await db.commit()
        
        return {"success": True}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
