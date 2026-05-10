"""
거래 내역 관리 라우터
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.transaction import Transaction, TransactionCategory, TransactionSource
from app.models.user import User
from app.services import gemini_service, exchange_rate_service, pdf_service, xrpl_service

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


# ============ Pydantic 스키마 ============

class TransactionCreate(BaseModel):
    """거래 생성 요청"""
    merchant_name: str
    amount_local: float
    currency: str
    category: Optional[str] = None
    source: str
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    items: Optional[List[dict]] = None
    receipt_image_url: Optional[str] = None
    receipt_ocr_text: Optional[str] = None
    bank_notification_text: Optional[str] = None


class TransactionUpdate(BaseModel):
    """거래 수정 요청"""
    category: Optional[str] = None
    merchant_name: Optional[str] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    """거래 응답"""
    id: str
    merchant_name: str
    amount_local: float
    currency: str
    amount_krw: float
    exchange_rate: float
    category: str
    category_confidence: float
    source: str
    transaction_date: str
    description: Optional[str]
    xrpl_recorded: bool
    xrpl_tx_hash: Optional[str]
    is_edited: bool
    created_at: str


class ReceiptAnalysisRequest(BaseModel):
    """영수증 분석 요청"""
    image_base64: str
    currency: str = "USD"


class BankNotificationRequest(BaseModel):
    """은행 알림 분석 요청"""
    notification_text: str
    currency: str = "USD"


class TransactionReportRequest(BaseModel):
    """거래 보고서 요청"""
    start_date: datetime
    end_date: datetime


# ============ API 엔드포인트 ============

@router.post("/analyze-receipt")
async def analyze_receipt(
    body: ReceiptAnalysisRequest,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    영수증 이미지 분석 및 거래 생성
    """
    try:
        # Gemini로 영수증 분석
        result = await gemini_service.analyze_receipt_image(
            body.image_base64,
            body.currency
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # 사용자 확인
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 거래 생성
        transaction = Transaction(
            user_id=user_id,
            merchant_name=result["merchant_name"],
            amount_local=Decimal(str(result["total_local"])),
            currency=result["currency"],
            amount_krw=Decimal(str(result["total_krw"])),
            exchange_rate=Decimal(str(result["exchange_rate"])),
            category=result["category"],
            category_confidence=Decimal(str(result["category_confidence"])),
            source=TransactionSource.RECEIPT,
            transaction_date=datetime.fromisoformat(result["date"]),
            description=result.get("description"),
            items=result.get("items"),
            receipt_ocr_text=body.image_base64,
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        return {
            "success": True,
            "transaction": _transaction_to_dict(transaction),
            "analysis": result,
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-bank-notification")
async def analyze_bank_notification(
    body: BankNotificationRequest,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    은행 알림 텍스트 분석 및 거래 자동 생성
    """
    try:
        # Gemini로 은행 알림 분석
        result = await gemini_service.analyze_bank_notification(
            body.notification_text,
            body.currency
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # 사용자 확인
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 거래 생성
        transaction = Transaction(
            user_id=user_id,
            merchant_name=result["merchant_name"],
            amount_local=Decimal(str(result["amount_local"])),
            currency=result["currency"],
            amount_krw=Decimal(str(result["amount_krw"])),
            exchange_rate=Decimal(str(result["exchange_rate"])),
            category=result["category"],
            category_confidence=Decimal(str(result["category_confidence"])),
            source=TransactionSource.BANK_NOTIFICATION,
            transaction_date=datetime.fromisoformat(result["date"]),
            description=result.get("description"),
            bank_notification_text=body.notification_text,
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        
        return {
            "success": True,
            "transaction": _transaction_to_dict(transaction),
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_transactions(
    user_id: uuid.UUID = Query(...),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    거래 내역 조회
    """
    try:
        query = select(Transaction).where(Transaction.user_id == user_id)
        
        # 날짜 필터
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)
        
        # 카테고리 필터
        if category:
            query = query.where(Transaction.category == category)
        
        result = await db.execute(query.order_by(Transaction.transaction_date.desc()))
        transactions = result.scalars().all()
        
        return {
            "success": True,
            "count": len(transactions),
            "transactions": [_transaction_to_dict(tx) for tx in transactions],
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: uuid.UUID,
    body: TransactionUpdate,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    거래 정보 수정 (카테고리 변경 등)
    """
    try:
        # 거래 조회
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.id == transaction_id,
                    Transaction.user_id == user_id,
                )
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # 수정 이력 저장
        if body.category and body.category != transaction.category:
            transaction.original_category = transaction.category
            transaction.category = body.category
            transaction.is_edited = True
            transaction.edited_at = datetime.now()
        
        if body.merchant_name:
            transaction.merchant_name = body.merchant_name
        
        if body.description:
            transaction.description = body.description
        
        await db.commit()
        await db.refresh(transaction)
        
        return {
            "success": True,
            "transaction": _transaction_to_dict(transaction),
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-xrpl/{transaction_id}")
async def record_to_xrpl(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    wallet_seed: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    거래를 XRPL에 기록
    """
    try:
        # 거래 조회
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.id == transaction_id,
                    Transaction.user_id == user_id,
                )
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # XRPL에 기록
        memo_data = {
            "type": "expense",
            "merchant": transaction.merchant_name,
            "amount": float(transaction.amount_local),
            "currency": transaction.currency,
            "category": transaction.category,
            "date": transaction.transaction_date.isoformat(),
            "description": transaction.description or "",
        }
        
        xrpl_result = await xrpl_service.record_transaction_with_memo(
            wallet_seed,
            memo_data
        )
        
        if not xrpl_result.get("success"):
            raise HTTPException(status_code=400, detail=xrpl_result.get("error"))
        
        # 거래 업데이트
        transaction.xrpl_tx_hash = xrpl_result["tx_hash"]
        transaction.xrpl_recorded = True
        
        await db.commit()
        await db.refresh(transaction)
        
        return {
            "success": True,
            "transaction": _transaction_to_dict(transaction),
            "xrpl_tx_hash": xrpl_result["tx_hash"],
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report")
async def generate_report(
    body: TransactionReportRequest,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    기간별 거래 내역 PDF 보고서 생성
    """
    try:
        # 사용자 정보 조회
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 거래 내역 조회
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date >= body.start_date,
                    Transaction.transaction_date <= body.end_date,
                )
            )
        )
        transactions = result.scalars().all()
        
        # PDF 생성
        pdf_buffer = await pdf_service.generate_transaction_report(
            user.name,
            [_transaction_to_dict(tx) for tx in transactions],
            body.start_date,
            body.end_date,
            user.default_currency,
        )
        
        return {
            "success": True,
            "pdf_size": len(pdf_buffer.getvalue()),
            "message": "PDF generated successfully",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    거래 삭제
    """
    try:
        result = await db.execute(
            select(Transaction).where(
                and_(
                    Transaction.id == transaction_id,
                    Transaction.user_id == user_id,
                )
            )
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        await db.delete(transaction)
        await db.commit()
        
        return {"success": True}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============ 헬퍼 함수 ============

def _transaction_to_dict(tx: Transaction) -> dict:
    """Transaction 객체를 딕셔너리로 변환"""
    return {
        "id": str(tx.id),
        "merchant_name": tx.merchant_name,
        "amount_local": float(tx.amount_local),
        "currency": tx.currency,
        "amount_krw": float(tx.amount_krw),
        "exchange_rate": float(tx.exchange_rate),
        "category": tx.category,
        "category_confidence": float(tx.category_confidence),
        "source": tx.source,
        "transaction_date": tx.transaction_date.isoformat(),
        "description": tx.description,
        "xrpl_recorded": tx.xrpl_recorded,
        "xrpl_tx_hash": tx.xrpl_tx_hash,
        "is_edited": tx.is_edited,
        "original_category": tx.original_category,
        "created_at": tx.created_at.isoformat(),
    }
