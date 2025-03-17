from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from utils.form_parser import parse_user_update_form
from api.dependencies import get_async_db, get_current_active_user
from crud import crud_user
from crud import crud_auth
import crud
from schemas.users import (
    UserProfile, UserProfileCreate,
    UserProfileUpdate, RecommendationResponse, TrustScoreUpdate
)
from schemas.auth import User, UserUpdate
from services.recommender import RecipeRecommender
from models.models import UserRole
from services.s3_service import upload_images_to_s3

router = APIRouter(prefix="/users", tags=["users"])
recommender = RecipeRecommender()

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user"""
    return current_user

@router.put("/me", response_model=User)
async def update_my_info(
    *,
    db: AsyncSession = Depends(get_async_db),
    form_data: tuple[Dict[str, Any], Optional[UploadFile]] = Depends(parse_user_update_form),
    current_user: User = Depends(get_current_active_user)
):
    """현재 사용자 정보 업데이트"""
    try:
        update_data, profile_image = form_data
        
        # 프로필 이미지가 있으면 S3에 업로드
        if profile_image and profile_image.filename:
            print(f"프로필 이미지 업로드 시작: {profile_image.filename}")
            image_urls = await upload_images_to_s3([profile_image])
            if image_urls:
                update_data["profile_image_url"] = image_urls[0]
                print(f"프로필 이미지 업로드 완료: {image_urls[0]}")
            else:
                print("프로필 이미지 업로드 실패")
        
        # 업데이트할 데이터가 있으면 UserUpdate 객체 생성
        if update_data:
            user_update = UserUpdate(**update_data)
            updated_user = await crud_auth.update_user_info(db, current_user.id, user_update)
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")
            return updated_user
        else:
            # 업데이트할 데이터가 없으면 현재 사용자 정보 반환
            return current_user
    except ValueError as e:
        print(f"사용자 정보 업데이트 중 오류: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"예상치 못한 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/{user_id}", response_model=User)
async def update_user_by_id(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """특정 사용자 정보 업데이트 (관리자 또는 본인만 가능)"""
    # 권한 체크: 본인 또는 관리자만 수정 가능
    if current_user.id != user_id and current_user.role != UserRole.CHEF:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to modify other users"
        )
    
    try:
        updated_user = await crud_auth.update_user_info(db, user_id, user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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