import uuid
from pydantic import BaseModel, Field


class WalletCreateIn(BaseModel):
    wallet_uuid: uuid.UUID | None = None
    balance: int = Field(default=0, ge=0, description="Initial balance")


class WalletOut(BaseModel):
    wallet_uuid: str
    balance: int
