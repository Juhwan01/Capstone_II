from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from services.ingredient_matcher import IngredientMatcher

router = APIRouter()

@router.get("/{name}")
async def get_matches(name : str , db: AsyncSession = Depends(get_db)):
    matcher = IngredientMatcher(db)
    matches = await matcher.find_matches_for_request(name)
    return matches
