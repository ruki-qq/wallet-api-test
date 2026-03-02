from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .operation import Operation


class Wallet(Base):
    """Model for wallets"""

    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    operations: Mapped[list["Operation"]] = relationship(back_populates="wallet")

    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_wallets_balance_non_negative"),
    )
