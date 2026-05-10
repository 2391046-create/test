import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import String, DateTime, ForeignKey, Numeric, Text, func, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionCategory(str, Enum):
    """거래 카테고리"""
    FOOD = "food"  # 식비
    TRANSPORT = "transport"  # 교통
    SHOPPING = "shopping"  # 쇼핑
    ENTERTAINMENT = "entertainment"  # 엔터테인먼트
    UTILITIES = "utilities"  # 공과금
    HEALTH = "health"  # 의료
    EDUCATION = "education"  # 교육
    ACCOMMODATION = "accommodation"  # 숙박
    CASH = "cash"  # 현금
    OTHER = "other"  # 기타


class TransactionSource(str, Enum):
    """거래 출처"""
    RECEIPT = "receipt"  # 영수증
    BANK_NOTIFICATION = "bank_notification"  # 은행 알림
    MANUAL = "manual"  # 수동 입력
    MENU_SCAN = "menu_scan"  # 메뉴판 스캔


class Transaction(Base):
    """사용자 거래 내역"""
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 기본 거래 정보
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False)  # 상호명
    amount_local: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)  # 현지 금액
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # 통화 (USD, JPY, KRW 등)
    amount_krw: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)  # 원화 환산 금액
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)  # 적용 환율
    
    # 카테고리 및 분류
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # 카테고리
    category_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)  # 카테고리 신뢰도 (%)
    
    # 거래 출처
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # 출처 (receipt, bank_notification, manual)
    
    # 거래 상세 정보
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # 거래 날짜/시간
    description: Mapped[str | None] = mapped_column(Text)  # 설명/메모
    items: Mapped[dict | None] = mapped_column(JSON)  # 구매 품목 리스트
    
    # 영수증/이미지 정보
    receipt_image_url: Mapped[str | None] = mapped_column(String(500))  # 영수증 이미지 URL
    receipt_ocr_text: Mapped[str | None] = mapped_column(Text)  # OCR 텍스트
    
    # 은행 알림 정보
    bank_notification_text: Mapped[str | None] = mapped_column(Text)  # 원본 은행 알림 텍스트
    
    # XRPL 블록체인 정보
    xrpl_tx_hash: Mapped[str | None] = mapped_column(String(64))  # XRPL 트랜잭션 해시
    xrpl_recorded: Mapped[bool] = mapped_column(Boolean, default=False)  # XRPL 기록 여부
    
    # 수정 이력
    original_category: Mapped[str | None] = mapped_column(String(50))  # 원본 카테고리 (수정된 경우)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)  # 수정 여부
    edited_at: Mapped[datetime | None] = mapped_column(DateTime)  # 수정 시간
    
    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    xrpl_record: Mapped["XrplRecord"] = relationship("XrplRecord", back_populates="transaction", uselist=False)


class XrplRecord(Base):
    """XRPL 블록체인 기록"""
    __tablename__ = "xrpl_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    
    # XRPL 정보
    tx_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)  # 트랜잭션 해시
    ledger_index: Mapped[int | None] = mapped_column(Integer)  # 레저 인덱스
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 상태 (pending, success, failed)
    memo_data: Mapped[dict] = mapped_column(JSON)  # Memo 필드 데이터
    
    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    # 관계
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="xrpl_record")
    wallet: Mapped["Wallet"] = relationship("Wallet")


class BudgetSetting(Base):
    """사용자 예산 설정"""
    __tablename__ = "budget_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # 예산 정보
    monthly_budget: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)  # 월간 예산
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # 통화
    
    # 카테고리별 예산
    category_budgets: Mapped[dict] = mapped_column(JSON)  # {"food": 500000, "transport": 200000, ...}
    
    # 타임스탐프
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 관계
    user: Mapped["User"] = relationship("User", back_populates="budget_setting")
