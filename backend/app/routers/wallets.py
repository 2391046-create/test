"""F01: XRPL 지갑 생성 및 잔액 조회"""
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet, WalletBalance
from app.schemas.wallet import BalanceInfo, WalletCreate, WalletResponse
from app.services import xrpl_service

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


@router.post("/", response_model=WalletResponse, status_code=201)
async def create_wallet(body: WalletCreate, db: AsyncSession = Depends(get_db)):
    """F01: XRPL 지갑 생성 → TrustLine 설정 → DB 저장"""
    # Validate user exists
    result = await db.execute(select(User).where(User.id == body.user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    if not settings.XRPL_ISSUER_ADDRESS:
        raise HTTPException(
            status_code=500,
            detail="XRPL_ISSUER_ADDRESS not configured. Run scripts/setup_issuer.py first.",
        )

    # Create XRPL wallet via testnet faucet (10-15s)
    xrpl_wallet = await xrpl_service.create_xrpl_wallet()

    # Set trust lines for each requested currency
    await xrpl_service.set_trust_lines(
        seed=xrpl_wallet["seed"],
        currencies=body.currencies,
        issuer=settings.XRPL_ISSUER_ADDRESS,
    )

    # Persist wallet with encrypted seed
    encrypted = xrpl_service.encrypt_seed(xrpl_wallet["seed"])
    wallet = Wallet(
        user_id=body.user_id,
        xrpl_address=xrpl_wallet["address"],
        encrypted_seed=encrypted,
    )
    db.add(wallet)
    await db.flush()

    # Seed initial XRP balance from XRPL
    balances_raw = await xrpl_service.get_account_balances(xrpl_wallet["address"])
    balance_objects = []
    for b in balances_raw:
        wb = WalletBalance(
            wallet_id=wallet.id,
            currency=b["currency"],
            amount=Decimal(b["amount"]),
        )
        db.add(wb)
        balance_objects.append(BalanceInfo(
            currency=b["currency"],
            amount=b["amount"],
            issuer=b.get("issuer"),
        ))

    await db.commit()
    await db.refresh(wallet)

    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        xrpl_address=wallet.xrpl_address,
        created_at=wallet.created_at,
        balances=balance_objects,
    )


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(wallet_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """F01: 지갑 조회 — XRPL에서 최신 잔액 동기화"""
    result = await db.execute(
        select(Wallet).where(Wallet.id == wallet_id).options(selectinload(Wallet.balances))
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Sync balances from XRPL
    balances_raw = await xrpl_service.get_account_balances(wallet.xrpl_address)

    # Update DB balances
    for b in balances_raw:
        existing = next(
            (wb for wb in wallet.balances if wb.currency == b["currency"]), None
        )
        if existing:
            existing.amount = Decimal(b["amount"])
        else:
            db.add(WalletBalance(
                wallet_id=wallet.id,
                currency=b["currency"],
                amount=Decimal(b["amount"]),
            ))
    await db.commit()

    balance_list = [
        BalanceInfo(currency=b["currency"], amount=b["amount"], issuer=b.get("issuer"))
        for b in balances_raw
    ]

    return WalletResponse(
        id=wallet.id,
        user_id=wallet.user_id,
        xrpl_address=wallet.xrpl_address,
        created_at=wallet.created_at,
        balances=balance_list,
    )
