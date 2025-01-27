from fastapi import APIRouter
from api.routes import transaction
from api.routes import chat

router = APIRouter()
router.include_router(transaction.router)
router.include_router(chat.router)