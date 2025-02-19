from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db, get_current_user
from services.ingredient_matcher import IngredientMatcher
from crud.crud_ingredient import CRUDIngredient
from schemas.ingredient import IngredientCreate
from typing import List


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

@router.post("/ingredients/multiple")
async def create_multiple_ingredients(
    payload: List[IngredientCreate],  
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """ 여러 개의 재료를 한 번에 등록 """
    crud = CRUDIngredient(db)  
    return await crud.create_multiple_ingredients(payload, user.id)


@router.delete("/ingredients/{ingredient_id}")
async def delete_ingredient(
    ingredient_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """ 단일 재료 삭제 """
    crud = CRUDIngredient(db)
    return await crud.delete_ingredient(ingredient_id, user.id)


@router.delete("/ingredients/multiple")
async def delete_multiple_ingredients(
    ingredient_ids: List[int],
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """ 여러 개의 재료 삭제 """
    crud = CRUDIngredient(db)
    return await crud.delete_multiple_ingredients(ingredient_ids, user.id)