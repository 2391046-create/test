"""
거래 내역 관리 라우터
- 영수증 이미지 인식
- 은행 알림 인식
- XRPL 기록
- PDF 보고서 생성
- 거래 수정
"""
import json
import uuid
from datetime import datetime
from typing import Optional, List
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet
from app.services import gemini_service, exchange_rate_service, pdf_service, xrpl_service

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


# ── 스키마 ──────────────────────────────────────────────────────────────

class ReceiptAnalyzeRequest(BaseModel):
    image_base64: str
    currency: str = "USD"
    user_id: str
    auto_record_xrpl: bool = False
    wallet_seed: Optional[str] = None


class BankNotifyRequest(BaseModel):
    notification_text: str
    currency: str = "USD"
    user_id: str
    auto_record_xrpl: bool = False
    wallet_seed: Optional[str] = None


class TransactionCreateRequest(BaseModel):
    user_id: str
    merchant_name: str
    amount_local: float
    currency: str
    category: str = "other"
    source: str = "manual"
    description: Optional[str] = None
    transaction_date: Optional[str] = None
    items: Optional[List[dict]] = None
    record_xrpl: bool = False
    wallet_seed: Optional[str] = None


class TransactionUpdateRequest(BaseModel):
    category: Optional[str] = None
    merchant_name: Optional[str] = None
    description: Optional[str] = None


class ReportRequest(BaseModel):
    user_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD


# ── 헬퍼 ────────────────────────────────────────────────────────────────

def _tx_to_dict(tx: Transaction) -> dict:
    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "merchant_name": tx.merchant_name,
        "amount_local": tx.amount_local,
        "currency": tx.currency,
        "amount_krw": tx.amount_krw,
        "exchange_rate": tx.exchange_rate,
        "category": tx.category,
        "category_confidence": tx.category_confidence,
        "original_category": tx.original_category,
        "source": tx.source,
        "transaction_date": tx.transaction_date.isoformat() if tx.transaction_date else None,
        "description": tx.description,
        "items": json.loads(tx.items_json or "[]"),
        "receipt_ocr_text": tx.receipt_ocr_text,
        "is_edited": tx.is_edited,
        "edited_at": tx.edited_at.isoformat() if tx.edited_at else None,
        "xrpl_recorded": tx.xrpl_recorded,
        "xrpl_tx_hash": tx.xrpl_tx_hash,
        "xrpl_recorded_at": tx.xrpl_recorded_at.isoformat() if tx.xrpl_recorded_at else None,
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
    }


async def _save_transaction(db: AsyncSession, tx_data: dict) -> Transaction:
    """거래 저장 + 환율 자동 계산"""
    amount_local = tx_data.get("amount_local", 0)
    currency = tx_data.get("currency", "USD")

    # 실시간 환율 조회
    rate = await exchange_rate_service.get_rate_to_krw(currency)
    amount_krw = round(amount_local * rate, 2)

    tx = Transaction(
        id=str(uuid.uuid4()),
        user_id=tx_data["user_id"],
        merchant_name=tx_data.get("merchant_name", "Unknown"),
        amount_local=amount_local,
        currency=currency,
        amount_krw=amount_krw,
        exchange_rate=rate,
        category=tx_data.get("category", "other"),
        category_confidence=tx_data.get("category_confidence", 0),
        source=tx_data.get("source", "manual"),
        transaction_date=datetime.fromisoformat(tx_data["date"]) if tx_data.get("date") else datetime.utcnow(),
        description=tx_data.get("description", ""),
        items_json=json.dumps(tx_data.get("items", []), ensure_ascii=False),
        receipt_ocr_text=tx_data.get("receipt_ocr_text"),
        xrpl_recorded=False,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


# ── 엔드포인트 ──────────────────────────────────────────────────────────

@router.post("/analyze-receipt")
async def analyze_receipt(body: ReceiptAnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """
    영수증 이미지 분석 → 자동 카테고리화 → DB 저장 → (선택) XRPL 기록
    """
    # 1. Gemini AI로 영수증 분석
    result = await gemini_service.analyze_receipt_image(body.image_base64, body.currency)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    # 2. DB 저장
    tx = await _save_transaction(db, {
        "user_id": body.user_id,
        "merchant_name": result["merchant_name"],
        "amount_local": result["total_local"],
        "currency": result["currency"],
        "category": result["category"],
        "category_confidence": result["category_confidence"],
        "source": "receipt",
        "date": result["date"],
        "description": result.get("description", ""),
        "items": result.get("items", []),
    })

    # 3. XRPL 기록 (선택)
    xrpl_result = None
    if body.auto_record_xrpl and body.wallet_seed:
        xrpl_result = xrpl_service.record_transaction_on_xrpl(body.wallet_seed, {
            "transaction_id": tx.id,
            "merchant_name": tx.merchant_name,
            "amount_local": tx.amount_local,
            "currency": tx.currency,
            "category": tx.category,
            "date": tx.transaction_date.strftime("%Y-%m-%d"),
        })
        if xrpl_result["success"]:
            tx.xrpl_recorded = True
            tx.xrpl_tx_hash = xrpl_result["tx_hash"]
            tx.xrpl_recorded_at = datetime.utcnow()
            await db.commit()

    return {
        "success": True,
        "transaction": _tx_to_dict(tx),
        "ai_analysis": result,
        "xrpl": xrpl_result,
    }


@router.post("/analyze-bank-notification")
async def analyze_bank_notification(body: BankNotifyRequest, db: AsyncSession = Depends(get_db)):
    """
    은행 앱 알림 텍스트 분석 → 자동 카테고리화 → DB 저장 → (선택) XRPL 기록
    """
    # 1. Gemini AI로 알림 분석
    result = await gemini_service.analyze_bank_notification(body.notification_text, body.currency)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    # 2. DB 저장
    tx = await _save_transaction(db, {
        "user_id": body.user_id,
        "merchant_name": result["merchant_name"],
        "amount_local": result["amount_local"],
        "currency": result["currency"],
        "category": result["category"],
        "category_confidence": result["category_confidence"],
        "source": "bank_notification",
        "date": result["date"],
        "description": result.get("description", ""),
        "items": [],
    })

    # 3. XRPL 기록 (선택)
    xrpl_result = None
    if body.auto_record_xrpl and body.wallet_seed:
        xrpl_result = xrpl_service.record_transaction_on_xrpl(body.wallet_seed, {
            "transaction_id": tx.id,
            "merchant_name": tx.merchant_name,
            "amount_local": tx.amount_local,
            "currency": tx.currency,
            "category": tx.category,
            "date": tx.transaction_date.strftime("%Y-%m-%d"),
        })
        if xrpl_result["success"]:
            tx.xrpl_recorded = True
            tx.xrpl_tx_hash = xrpl_result["tx_hash"]
            tx.xrpl_recorded_at = datetime.utcnow()
            await db.commit()

    return {
        "success": True,
        "transaction": _tx_to_dict(tx),
        "ai_analysis": result,
        "xrpl": xrpl_result,
    }


@router.post("/create")
async def create_transaction(body: TransactionCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    수동 거래 생성
    """
    tx = await _save_transaction(db, {
        "user_id": body.user_id,
        "merchant_name": body.merchant_name,
        "amount_local": body.amount_local,
        "currency": body.currency,
        "category": body.category,
        "category_confidence": 100.0,
        "source": body.source,
        "date": body.transaction_date or datetime.utcnow().strftime("%Y-%m-%d"),
        "description": body.description or "",
        "items": body.items or [],
    })

    # XRPL 기록 (선택)
    if body.record_xrpl and body.wallet_seed:
        xrpl_result = xrpl_service.record_transaction_on_xrpl(body.wallet_seed, {
            "transaction_id": tx.id,
            "merchant_name": tx.merchant_name,
            "amount_local": tx.amount_local,
            "currency": tx.currency,
            "category": tx.category,
            "date": tx.transaction_date.strftime("%Y-%m-%d"),
        })
        if xrpl_result["success"]:
            tx.xrpl_recorded = True
            tx.xrpl_tx_hash = xrpl_result["tx_hash"]
            tx.xrpl_recorded_at = datetime.utcnow()
            await db.commit()

    return {"success": True, "transaction": _tx_to_dict(tx)}


@router.get("/list")
async def list_transactions(
    user_id: str = Query(...),
    category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
):
    """거래 목록 조회 (필터링 지원)"""
    stmt = select(Transaction).where(Transaction.user_id == user_id)

    if category:
        stmt = stmt.where(Transaction.category == category)
    if start_date:
        stmt = stmt.where(Transaction.transaction_date >= datetime.fromisoformat(start_date))
    if end_date:
        stmt = stmt.where(Transaction.transaction_date <= datetime.fromisoformat(end_date + "T23:59:59"))

    stmt = stmt.order_by(Transaction.transaction_date.desc()).limit(limit)
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    return {
        "success": True,
        "transactions": [_tx_to_dict(t) for t in transactions],
        "total": len(transactions),
    }


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """거래 단건 조회"""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
    return {"success": True, "transaction": _tx_to_dict(tx)}


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    body: TransactionUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    거래 수정 (카테고리 변경 등) - 수정 이력 자동 저장
    """
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")

    if body.category:
        if not tx.original_category:
            tx.original_category = tx.category  # 최초 수정 시 원본 보존
        tx.category = body.category

    if body.merchant_name:
        tx.merchant_name = body.merchant_name

    if body.description is not None:
        tx.description = body.description

    tx.is_edited = True
    tx.edited_at = datetime.utcnow()
    await db.commit()
    await db.refresh(tx)

    return {"success": True, "transaction": _tx_to_dict(tx)}


@router.post("/{transaction_id}/record-xrpl")
async def record_to_xrpl(
    transaction_id: str,
    wallet_seed: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    특정 거래를 XRPL 블록체인에 기록
    """
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")

    xrpl_result = xrpl_service.record_transaction_on_xrpl(wallet_seed, {
        "transaction_id": tx.id,
        "merchant_name": tx.merchant_name,
        "amount_local": tx.amount_local,
        "currency": tx.currency,
        "category": tx.category,
        "date": tx.transaction_date.strftime("%Y-%m-%d") if tx.transaction_date else "",
    })

    if not xrpl_result["success"]:
        raise HTTPException(status_code=400, detail=xrpl_result["error"])

    tx.xrpl_recorded = True
    tx.xrpl_tx_hash = xrpl_result["tx_hash"]
    tx.xrpl_recorded_at = datetime.utcnow()
    await db.commit()

    return {
        "success": True,
        "tx_hash": xrpl_result["tx_hash"],
        "transaction_id": transaction_id,
    }


@router.post("/generate-report")
async def generate_report(body: ReportRequest, db: AsyncSession = Depends(get_db)):
    """
    기간별 거래 내역 PDF 증빙자료 생성
    """
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == body.user_id)
        .where(Transaction.transaction_date >= datetime.fromisoformat(body.start_date))
        .where(Transaction.transaction_date <= datetime.fromisoformat(body.end_date + "T23:59:59"))
        .order_by(Transaction.transaction_date.desc())
    )
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    if not transactions:
        raise HTTPException(status_code=404, detail="해당 기간의 거래 내역이 없습니다")

    tx_list = [_tx_to_dict(t) for t in transactions]

    # PDF 생성
    pdf_bytes = pdf_service.generate_transaction_report(
        transactions=tx_list,
        start_date=body.start_date,
        end_date=body.end_date,
        user_name=body.user_id,
    )

    filename = f"report_{body.start_date}_{body.end_date}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """거래 삭제"""
    result = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
    await db.delete(tx)
    await db.commit()
    return {"success": True, "message": "삭제 완료"}
