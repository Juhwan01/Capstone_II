from fastapi import APIRouter
from api.routes import auth, users, recipes, permissions, ingredients

router = APIRouter()
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(recipes.router)
router.include_router(permissions.router)
router.include_router(ingredients.router)
