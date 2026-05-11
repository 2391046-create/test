"""
사용자 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)

    # 통화/국가 설정
    default_currency = Column(String, default="USD")
    preferred_country = Column(String, default="USA")

    # 예산 설정
    monthly_budget = Column(Float, nullable=True)
    budget_currency = Column(String, default="USD")

    # 카테고리별 예산 (JSON string)
    category_budgets = Column(String, default="{}")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
