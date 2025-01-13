from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import Field
from api.dependencies import get_async_db, get_current_active_user
from crud import crud_recipe, crud_user
from models.models import User
from schemas.recipes import Recipe, RecipeCreate, RecipeUpdate,RecipeRating
from schemas.users import UserProfile
from services.recommender import RecipeRecommender

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

@router.get("/", response_model=List[Recipe])
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
    return recipes

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

@router.post("/{recipe_id}/rating", response_model=UserProfile)
async def rate_recipe(
    *,
    db: AsyncSession = Depends(get_async_db),
    recipe_id: int,
    rating_in: RecipeRating,
    current_user: User = Depends(get_current_active_user)
):
    """Rate a recipe and update Q-values"""
    # Check if recipe exists
    recipe = await crud_recipe.recipe.get(db=db, id=recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found"
        )
    
    # Update user profile with rating
    user_profile = await crud_user.user.get_profile(db=db, user_id=current_user.id)
    if not user_profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )
    
    # Update rating
    ratings = user_profile.ratings or {}
    ratings[str(recipe_id)] = rating_in.rating
    user_profile.ratings = ratings
    
    # Add to history if not exists
    if recipe_id not in user_profile.recipe_history:
        user_profile.recipe_history.append(recipe_id)
    
    # Update Q-value based on rating
    recommender = RecipeRecommender()
    await recommender.update_q_value(
        db=db,
        user_id=current_user.id,
        recipe_id=recipe_id,
        reward=rating_in.rating / 5.0  # Normalize rating to 0-1 range
    )
    
    await db.commit()
    await db.refresh(user_profile)
    return user_profile