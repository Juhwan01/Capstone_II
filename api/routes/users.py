from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_async_db, get_current_active_user
from crud import crud_user
from crud import crud_auth
import crud
from schemas.users import (
    UserProfile, UserProfileCreate,
    UserProfileUpdate, RecommendationResponse, TrustScoreUpdate
)
from schemas.auth import User
from services.recommender import RecipeRecommender
from models.models import UserRole

router = APIRouter(prefix="/users", tags=["users"])
recommender = RecipeRecommender()

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user"""
    return current_user

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    사용자 ID로 사용자 정보 조회
    """
    # 사용자 조회
    user = await crud_auth.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

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

@router.put("/me/trust-score", response_model=User)
async def update_my_trust_score(
    *,
    db: AsyncSession = Depends(get_async_db),
    score_update: TrustScoreUpdate,  # request body로 변경
    current_user: User = Depends(get_current_active_user)
):
    """Update user trust score and role"""
    updated_user = await crud.update_user_role(
        db=db,
        user_id=current_user.id,
        trust_score=score_update.trust_score
    )
    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return updated_user

@router.get("/me/permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's permissions based on role"""
    permissions = {
        "can_write_global_announcements": current_user.role == UserRole.CHEF,
        "can_create_recipe_class": current_user.role == UserRole.CHEF,
        "can_host_bulk_purchase": current_user.role in [UserRole.CHEF, UserRole.MASTER],
        "can_host_regular_purchase": current_user.role in [UserRole.CHEF, UserRole.MASTER, UserRole.EXPERT],
    }
    return {
        "role": current_user.role,
        "trust_score": current_user.trust_score,
        "permissions": permissions
    }