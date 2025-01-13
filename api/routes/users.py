from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_async_db, get_current_active_user
from crud import crud_user
from schemas.users import (
    UserProfile, UserProfileCreate,
    UserProfileUpdate, RecommendationResponse
)
from schemas.auth import User
from services.recommender import RecipeRecommender

router = APIRouter(prefix="/users", tags=["users"])
recommender = RecipeRecommender()

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user"""
    return current_user

@router.get("/me/profile", response_model=UserProfile)
async def get_my_profile(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile"""
    profile = await crud_user.user.get_profile(
        db=db,
        user_id=current_user.id
    )
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    return profile

@router.put("/me/profile", response_model=UserProfile)
async def update_my_profile(
    *,
    db: AsyncSession = Depends(get_async_db),
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile"""
    profile = await crud_user.user.get_profile(
        db=db,
        user_id=current_user.id
    )
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    profile = await crud_user.user.update(
        db=db,
        db_obj=profile,
        obj_in=profile_in
    )
    return profile

@router.put("/me/ingredients", response_model=UserProfile)
async def update_my_ingredients(
    *,
    db: AsyncSession = Depends(get_async_db),
    ingredients: Dict[str, float],
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's ingredients"""
    profile = await crud_user.user.update_ingredients(
        db=db,
        user_id=current_user.id,
        ingredients=ingredients
    )
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    return profile

@router.get("/me/recommendations", response_model=List[RecommendationResponse])
async def get_my_recommendations(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get recipe recommendations for current user"""
    recommendations = await recommender.get_recommendations(
        db=db,
        user_id=current_user.id
    )
    return recommendations