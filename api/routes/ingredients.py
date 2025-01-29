from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db
from services.ingredient_matcher import IngredientMatcher

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

@router.get("/{name}")
async def get_matches(name : str , db: AsyncSession = Depends(get_async_db)):
    matcher = IngredientMatcher(db)
    matches = await matcher.find_matches_for_request(name)
    return matches
