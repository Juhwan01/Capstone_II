from fastapi import APIRouter
from api.routes import auth, users, recipes, permissions, ingredients, transaction, chat

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(recipes.router)
router.include_router(permissions.router)
router.include_router(ingredients.router)
router.include_router(transaction.router)
router.include_router(chat.router)
