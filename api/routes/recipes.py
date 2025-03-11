from typing import List, Dict
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import Field
from api.dependencies import get_async_db, get_current_active_user
from crud import crud_recipe, crud_user
from models.models import User
from schemas.recipes import Recipe, RecipeCreate, RecipeUpdate,RecipeRating
from schemas.users import UserProfile
from services import RecipeRecommender,RecipeService
from collections import defaultdict

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/", response_model=Recipe)
async def create_recipe(
    *,
    db: AsyncSession = Depends(get_async_db),
    recipe_in: RecipeCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Create new recipe"""
    recipe = await crud_recipe.recipe.create_with_owner(
        db=db,
        obj_in=recipe_in,
        owner_id=current_user.id
    )
    return recipe

@router.get("/", response_model=Dict[str, List[Recipe]])
async def list_recipes(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """List all recipes"""
    recipes = await crud_recipe.recipe.get_multi(
        db=db,
        skip=skip,
        limit=limit
    )
    print(recipes)
    response_data = defaultdict(list)
    for recipe in recipes:
        response_data[recipe.category].append(recipe)
    return response_data  

@router.get("/{recipe_id}", response_model=Recipe)
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recipe by ID"""
    recipe = await crud_recipe.recipe.get(db=db, id=recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found"
        )
    return recipe

@router.put("/{recipe_id}", response_model=Recipe)
async def update_recipe(
    *,
    db: AsyncSession = Depends(get_async_db),
    recipe_id: int,
    recipe_in: RecipeUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update recipe"""
    recipe = await crud_recipe.recipe.get(db=db, id=recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found"
        )
    if recipe.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    recipe = await crud_recipe.recipe.update(
        db=db,
        db_obj=recipe,
        obj_in=recipe_in
    )
    return recipe

@router.delete("/{recipe_id}")
async def delete_recipe(
    *,
    db: AsyncSession = Depends(get_async_db),
    recipe_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete recipe"""
    recipe = await crud_recipe.recipe.get(db=db, id=recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found"
        )
    if recipe.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    await crud_recipe.recipe.remove(db=db, id=recipe_id)
    return {"success": True}

@router.get("/recommendations/{user_id}/select/{recipe_id}", response_model=Recipe)
async def select_recommended_recipe(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: int,
    recipe_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """추천된 레시피 선택 API 엔드포인트"""
    recipe_service = RecipeService()
    return await recipe_service.select_recipe(db, user_id, recipe_id)

@router.post("/recommendations/{recipe_id}/rate", response_model=UserProfile)
async def rate_recipe(
    *,
    db: AsyncSession = Depends(get_async_db),
    recipe_id: int,
    rating: float = Body(..., ge=0, le=5),
    current_user: User = Depends(get_current_active_user)
):
    """레시피 평가 API 엔드포인트"""
    recipe_service = RecipeService()
    return await recipe_service.rate_recipe(db, current_user.id, recipe_id, rating)