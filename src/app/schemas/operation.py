from enum import Enum
from pydantic import BaseModel, Field


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationIn(BaseModel):
    operation_type: OperationType
    amount: int = Field(gt=0, description="Amount of deposit")
