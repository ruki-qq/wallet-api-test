import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UUID,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


if TYPE_CHECKING:
    from .wallet import Wallet


class OperationType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class Operation(Base):
    """Model for wallet operations"""

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    operation_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType, name="operation_type_enum", native_enum=True),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    wallet: Mapped["Wallet"] = relationship(back_populates="operations")

    __table_args__ = (
        UniqueConstraint(
            "wallet_id",
            "idempotency_key",
            name="uq_wallet_ops_wallet_id_idempotency_key",
        ),
        CheckConstraint("amount > 0", name="ck_wallet_ops_amount_positive"),
        CheckConstraint(
            "balance_after >= 0", name="ck_wallet_ops_balance_after_non_negative"
        ),
    )
