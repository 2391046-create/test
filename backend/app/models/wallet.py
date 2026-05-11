"""
XRPL 지갑 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from app.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, default="My Wallet")
    address = Column(String, nullable=False, unique=True)
    public_key = Column(String, nullable=True)

    # 암호화된 seed (실제 서비스에서는 더 강력한 암호화 필요)
    encrypted_seed = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
