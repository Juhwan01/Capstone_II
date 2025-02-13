from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db, get_current_user, get_current_active_user
from services.ingredient_matcher import IngredientMatcher
from crud.crud_ingredient import CRUDIngredient
from schemas.ingredient import IngredientCreate

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

@router.get("/{name}")
async def get_matches(name : str , db: AsyncSession = Depends(get_async_db)):
    matcher = IngredientMatcher(db)
    matches = await matcher.find_matches_for_request(name)
    return matches

@router.post("/create")
async def create_request(payload:IngredientCreate,user=Depends(get_current_user),db=Depends(get_async_db)):
    crud = CRUDIngredient(db)
    request = await crud.create_ingredient(payload, user.id)
    return request

@router.post("/test")
async def get_ingredient(user=Depends(get_current_user), db=Depends(get_async_db)):
    crud = CRUDIngredient(db)
    return await crud.get_ingredient(user_id=user.id)