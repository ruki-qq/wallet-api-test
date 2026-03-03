import uuid

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Operation, Wallet
from core.models.operation import OperationType


class WalletNotFoundError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class WalletAlreadyExistsError(Exception):
    pass


async def create_wallet(
    session,
    wallet_id: uuid.UUID | None = None,
    initial_balance: int = 0,
) -> tuple[uuid.UUID, int]:
    """
    Create new wallet

    Args:
        session: AsyncSession - db async session
        wallet_id: uuid - wallet id to create new wallet
        initial_balance: int - initial wallet balance

    Raises:
        WalletAlreadyExistsError - if wallet already exists
    Returns:
        wallet_uuid: uuid - wallet id
        balance: int - initial wallet balance
    """

    wallet_id = wallet_id or uuid.uuid4()

    try:
        async with session.begin():
            wallet = Wallet(id=wallet_id, balance=initial_balance)
            session.add(wallet)
            await session.flush()

        return wallet_id, int(initial_balance)

    except IntegrityError:
        await session.rollback()
        raise WalletAlreadyExistsError


async def get_wallet_balance(session: AsyncSession, wallet_id: uuid.UUID) -> int:
    """
    Get wallet balance

    Args:
        session: AsyncSession - db async session
        wallet_id: uuid - wallet id to get balance

    Raises:
        WalletNotFoundError - if wallet not found
    Returns:
        wallet balance: int - current wallet balance
    """

    balance = await session.scalar(select(Wallet.balance).where(Wallet.id == wallet_id))
    if balance is None:
        raise WalletNotFoundError
    return balance


async def apply_operation(
    session: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType,
    amount: int,
    idempotency_key: str,
) -> int:
    """
    Apply operation(deposit, withdraw)

    Args:
        session: AsyncSession - db async session
        wallet_id: uuid - wallet id to apply operation
        operation_type: OperationType - DEPOSIT, WITHDRAW
        amount: int - amount to apply
        idempotency_key: uuid - idempotency key

    Raises:
        WalletNotFoundError - if wallet not found
        InsufficientFundsError - if wallet balance is not enough to withdraw

    Returns:
        balance after applying operation
    """

    async with session.begin():
        wallet = await session.get(Wallet, wallet_id)
        if wallet is None:
            raise WalletNotFoundError

        existing_balance = await session.scalar(
            select(Operation.balance_after).where(
                Operation.wallet_id == wallet_id,
                Operation.idempotency_key == idempotency_key,
            )
        )
        if existing_balance is not None:
            return existing_balance

        wallet_balance = wallet.balance
        if operation_type == OperationType.WITHDRAW:
            if wallet_balance - amount < 0:
                raise InsufficientFundsError
            amount = -amount

        await session.execute(
            update(Wallet)
            .where(Wallet.id == wallet_id)
            .values(balance=wallet_balance + amount)
        )

        balance_after = wallet_balance + amount

        operation = Operation(
            wallet_id=wallet_id,
            operation_type=operation_type,
            amount=abs(amount),
            idempotency_key=idempotency_key,
            balance_after=balance_after,
        )
        session.add(operation)
        await session.flush()

        return balance_after
