import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class ChargeRequest(BaseModel):
    recipient_wallet_id: uuid.UUID
    sender_seed: str
    amount: str
    currency: str = "XRP"
    issuer: str | None = None


class ExchangeRequest(BaseModel):
    wallet_id: uuid.UUID
    from_currency: str
    to_currency: str
    from_max: str
    to_amount: str | None = None   # None이면 DEX 환율로 자동 계산
    slippage_pct: float = 1.0      # 허용 슬리피지 % (기본 1%)

    @field_validator("to_amount", mode="before")
    @classmethod
    def coerce_null_string(cls, v):
        if v in (None, "", "null", "NULL", "none", "None"):
            return None
        return v


class TransactionResponse(BaseModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    tx_type: str
    xrpl_tx_hash: str
    status: str
    amount: Decimal | None
    currency: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExchangeResponse(BaseModel):
    transaction: TransactionResponse
    exchanged_amount: str
    rate: str | None = None
