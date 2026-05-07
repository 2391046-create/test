"""F02: 생활비 충전(Payment) / F03: 자동 환전(PathPayment)"""
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.transaction import XrplTransaction
from app.models.wallet import Wallet, WalletBalance
from app.schemas.transaction import (
    ChargeRequest,
    ExchangeRequest,
    ExchangeResponse,
    TransactionResponse,
)
from app.services import xrpl_service

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


async def _get_wallet_or_404(wallet_id: uuid.UUID, db: AsyncSession) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


async def _upsert_balance(
    db: AsyncSession, wallet_id: uuid.UUID, currency: str, delta: Decimal
):
    result = await db.execute(
        select(WalletBalance).where(
            WalletBalance.wallet_id == wallet_id,
            WalletBalance.currency == currency,
        )
    )
    wb = result.scalar_one_or_none()
    if wb:
        wb.amount = wb.amount + delta
    else:
        db.add(WalletBalance(wallet_id=wallet_id, currency=currency, amount=delta))


@router.post("/charge", response_model=TransactionResponse, status_code=201)
async def charge_wallet(body: ChargeRequest, db: AsyncSession = Depends(get_db)):
    """F02: 부모 → 학생 생활비 송금 (XRPL Payment)"""
    recipient = await _get_wallet_or_404(body.recipient_wallet_id, db)

    issuer = body.issuer or settings.XRPL_ISSUER_ADDRESS or None

    try:
        result = await xrpl_service.send_payment(
            sender_seed=body.sender_seed,
            recipient_address=recipient.xrpl_address,
            amount=body.amount,
            currency=body.currency,
            issuer=issuer,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    tx = XrplTransaction(
        wallet_id=recipient.id,
        tx_type="Payment",
        xrpl_tx_hash=result["tx_hash"],
        status=result["status"],
        amount=Decimal(body.amount),
        currency=body.currency.upper(),
    )
    db.add(tx)

    # Update recipient balance optimistically
    if result["status"] == "success":
        await _upsert_balance(db, recipient.id, body.currency.upper(), Decimal(body.amount))

    await db.commit()
    await db.refresh(tx)
    return tx


@router.post("/exchange", response_model=ExchangeResponse, status_code=201)
async def exchange_currency(body: ExchangeRequest, db: AsyncSession = Depends(get_db)):
    """F03: 다중통화 자동 환전 (XRPL PathPaymentStrictReceive)"""
    if not settings.XRPL_ISSUER_ADDRESS:
        raise HTTPException(
            status_code=500,
            detail="XRPL_ISSUER_ADDRESS not configured. Run scripts/setup_issuer.py first.",
        )

    wallet = await _get_wallet_or_404(body.wallet_id, db)
    seed = xrpl_service.decrypt_seed(wallet.encrypted_seed)

    try:
        result = await xrpl_service.path_payment(
            sender_seed=seed,
            from_currency=body.from_currency,
            from_max=body.from_max,
            to_currency=body.to_currency,
            to_amount=body.to_amount,
            issuer=settings.XRPL_ISSUER_ADDRESS,
            slippage_pct=body.slippage_pct,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    tx = XrplTransaction(
        wallet_id=wallet.id,
        tx_type="PathPayment",
        xrpl_tx_hash=result["tx_hash"],
        status=result["status"],
        amount=Decimal(result["exchanged_amount"]),
        currency=body.to_currency.upper(),
        memo=f"{body.from_currency}→{body.to_currency} rate={result.get('rate')}",
    )
    db.add(tx)

    # Update balances optimistically
    if result["status"] == "success":
        await _upsert_balance(
            db, wallet.id, body.from_currency.upper(), -Decimal(result["spent_amount"])
        )
        await _upsert_balance(
            db, wallet.id, body.to_currency.upper(), Decimal(result["exchanged_amount"])
        )

    await db.commit()
    await db.refresh(tx)

    return ExchangeResponse(
        transaction=tx,
        exchanged_amount=result["exchanged_amount"],
        rate=result.get("rate"),
    )


@router.get("/wallet/{wallet_id}", response_model=list[TransactionResponse])
async def list_transactions(wallet_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """지갑의 트랜잭션 내역 조회"""
    await _get_wallet_or_404(wallet_id, db)
    result = await db.execute(
        select(XrplTransaction)
        .where(XrplTransaction.wallet_id == wallet_id)
        .order_by(XrplTransaction.created_at.desc())
    )
    return result.scalars().all()
