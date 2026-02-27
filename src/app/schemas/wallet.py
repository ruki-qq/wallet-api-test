from pydantic import BaseModel


class WalletOut(BaseModel):
    wallet_uuid: str
    balance: int
