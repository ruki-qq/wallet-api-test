import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import OperationIn, WalletCreateIn, WalletOut
from app.services.wallet import (
    InsufficientFundsError,
    WalletAlreadyExistsError,
    WalletNotFoundError,
    apply_operation,
    create_wallet,
    get_wallet_balance,
)
from core import db_helper, get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletOut, status_code=status.HTTP_201_CREATED)
async def create_wallet_endpoint(
    payload: WalletCreateIn,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        logger.debug("Trying to create wallet with payload %s", payload)
        wallet_id, balance = await create_wallet(
            session=session,
            wallet_id=payload.wallet_uuid,
            initial_balance=payload.balance,
        )
    except WalletAlreadyExistsError:
        logger.debug("Wallet with uuid %s already exist", payload.wallet_uuid)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Wallet already exists"
        )

    return WalletOut(wallet_uuid=str(wallet_id), balance=balance)


@router.get("/{wallet_uuid}", response_model=WalletOut)
async def get_wallet(
    wallet_uuid: uuid.UUID,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    try:
        logger.debug("Trying to get wallet with uuid %s", wallet_uuid)
        balance = await get_wallet_balance(session, wallet_uuid)
    except WalletNotFoundError:
        logger.debug("Wallet with uuid %s not found", wallet_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
        )
    return WalletOut(wallet_uuid=str(wallet_uuid), balance=balance)


@router.post("/{wallet_uuid}/operation", response_model=WalletOut)
async def wallet_operation(
    wallet_uuid: uuid.UUID,
    payload: OperationIn,
    session: AsyncSession = Depends(db_helper.session_dependency),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        logger.debug("Generating random idempotency_key")
        idempotency_key = str(uuid.uuid4())

    try:
        logger.debug("Trying to apply operation with payload %s", payload)
        new_balance = await apply_operation(
            session=session,
            wallet_id=wallet_uuid,
            operation_type=payload.operation_type,
            amount=payload.amount,
            idempotency_key=idempotency_key,
        )
    except WalletNotFoundError:
        logger.debug("Wallet with uuid %s not found", wallet_uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found"
        )
    except InsufficientFundsError:
        logger.debug("Wallet with uuid %s has insufficient funds", wallet_uuid)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Insufficient funds"
        )

    return WalletOut(wallet_uuid=str(wallet_uuid), balance=new_balance)
