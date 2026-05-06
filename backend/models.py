"""
데이터베이스 모델 정의
SQLAlchemy ORM 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")


class Transaction(Base):
    """거래 내역 모델"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # 거래 정보
    merchant = Column(String(255), index=True)
    amount = Column(Float)
    currency = Column(String(10), default="KRW")
    category = Column(String(50), index=True)
    description = Column(Text, nullable=True)
    
    # 날짜
    transaction_date = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # XRPL 블록체인 정보
    xrpl_tx_hash = Column(String(255), nullable=True, unique=True, index=True)
    xrpl_memo = Column(Text, nullable=True)
    is_recorded_on_blockchain = Column(Boolean, default=False)
    
    # 신뢰도
    confidence = Column(Float, default=0.0)
    raw_text = Column(Text, nullable=True)
    
    # 관계
    user = relationship("User", back_populates="transactions")


class Budget(Base):
    """예산 모델"""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # 예산 정보
    category = Column(String(50), index=True)
    amount = Column(Float)
    currency = Column(String(10), default="KRW")
    month_year = Column(String(7), index=True)  # YYYY-MM 형식
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    user = relationship("User", back_populates="budgets")


class XRPLRecord(Base):
    """XRPL 기록 모델"""
    __tablename__ = "xrpl_records"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), index=True)
    
    # 트랜잭션 정보
    tx_hash = Column(String(255), unique=True, index=True)
    account = Column(String(255))
    destination = Column(String(255))
    amount = Column(String(50))
    
    # 메모 (JSON 형식의 지출 정보)
    memo_data = Column(Text)
    
    # 상태
    status = Column(String(50), default="pending")  # pending, confirmed, failed
    ledger_index = Column(Integer, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
