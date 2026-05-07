import uuid
from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
