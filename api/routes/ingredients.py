from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db, get_current_active_user, get_current_user
from models.models import Ingredient
from schemas.auth import User
from services.ingredient_matcher import IngredientMatcher
from crud.crud_ingredient import CRUDIngredient
from schemas.ingredient import IngredientCreate, IngredientUpdate, UserIngredientsResponse
from typing import List, Optional


router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

@router.get("/my", response_model=List[UserIngredientsResponse])
async def get_my_ingredients(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    category: Optional[str] = None,  # 카테고리로 필터링
    sort_by: Optional[str] = 'expiry_date',  # 정렬 기준
    ascending: bool = True  # 정렬 방향
):
    """현재 사용자의 식재료 조회 (필터링 및 정렬 지원)"""
    query = select(Ingredient).where(Ingredient.user_id == current_user.id)
    
    # 카테고리 필터링
    if category:
        query = query.where(Ingredient.category == category)
    
    # 정렬
    if sort_by == 'expiry_date':
        query = query.order_by(Ingredient.expiry_date.asc() if ascending else Ingredient.expiry_date.desc())
    elif sort_by == 'name':
        query = query.order_by(Ingredient.name.asc() if ascending else Ingredient.name.desc())
    elif sort_by == 'amount':
        query = query.order_by(Ingredient.amount.asc() if ascending else Ingredient.amount.desc())
    
    result = await db.execute(query)
    ingredients = result.scalars().all()
    
    return ingredients

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

@router.put("/ingredients/{ingredient_id}")
async def update_ingredient(
            ingredient_id: int,
            payload: IngredientUpdate,
            user=Depends(get_current_user),
            db: AsyncSession = Depends(get_async_db)
        ):
            """ 특정 재료 업데이트 """
            crud = CRUDIngredient(db)
            return await crud.update_ingredient(ingredient_id, payload, user.id)