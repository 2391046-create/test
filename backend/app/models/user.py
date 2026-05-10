import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 사용자 설정
    default_currency: Mapped[str] = mapped_column(String(3), default="KRW")  # 기본 통화
    country: Mapped[str | None] = mapped_column(String(50))  # 국가
    
    # 관계
    wallets: Mapped[list["Wallet"]] = relationship("Wallet", back_populates="user")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user")
    budget_setting: Mapped["BudgetSetting"] = relationship("BudgetSetting", back_populates="user", uselist=False)
