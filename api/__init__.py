from fastapi import APIRouter
from api.routes import (
    auth,
    users,
    recipes,
    permissions,
    ingredients,
    transaction,
    chat,
    sale,
    group_purchases,
    receipts,
    group_chat
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(recipes.router)
router.include_router(permissions.router)
router.include_router(ingredients.router)
router.include_router(transaction.router)
router.include_router(chat.router)
router.include_router(group_purchases.router)
router.include_router(receipts.router)
router.include_router(sale.router)
router.include_router(group_chat.router)