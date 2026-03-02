from pydantic import BaseModel, Field

from core.models.operation import OperationType


class OperationIn(BaseModel):
    operation_type: OperationType
    amount: int = Field(gt=0, description="Amount of deposit or withdraw")
