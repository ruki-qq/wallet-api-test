__all__ = ("router",)

from fastapi import APIRouter

from .wallet import router as wallet_router

router = APIRouter(prefix="/api", tags=["api"])
router.include_router(wallet_router, tags=["wallets"])
