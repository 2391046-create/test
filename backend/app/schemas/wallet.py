import uuid
from datetime import datetime

from pydantic import BaseModel


class WalletCreate(BaseModel):
    user_id: uuid.UUID
    currencies: list[str] = ["USD", "EUR", "KRW"]


class BalanceInfo(BaseModel):
    currency: str
    amount: str
    issuer: str | None = None


class WalletResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    xrpl_address: str
    created_at: datetime
    balances: list[BalanceInfo] = []

    model_config = {"from_attributes": True}
