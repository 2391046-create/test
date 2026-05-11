"""
거래 내역 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, ForeignKey
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # 거래 기본 정보
    merchant_name = Column(String, nullable=False)
    amount_local = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    amount_krw = Column(Float, default=0)
    exchange_rate = Column(Float, default=0)

    # 카테고리
    category = Column(String, default="other")
    category_confidence = Column(Float, default=0)
    original_category = Column(String, nullable=True)  # 수정 전 카테고리

    # 출처 (receipt / bank_notification / manual)
    source = Column(String, default="manual")

    # 날짜
    transaction_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 상세 정보
    description = Column(Text, nullable=True)
    items_json = Column(Text, default="[]")  # JSON string

    # 영수증 관련
    receipt_image_url = Column(String, nullable=True)
    receipt_ocr_text = Column(Text, nullable=True)

    # 수정 이력
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)

    # XRPL 기록
    xrpl_recorded = Column(Boolean, default=False)
    xrpl_tx_hash = Column(String, nullable=True)
    xrpl_recorded_at = Column(DateTime, nullable=True)
