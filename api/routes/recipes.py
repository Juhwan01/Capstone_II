from typing import List, Dict, Optional
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import Field
from api.dependencies import get_async_db, get_current_active_user
from crud import crud_recipe, crud_user
from models.models import User
from schemas.recipes import Recipe, RecipeCreate, RecipeUpdate,RecipeRating
from schemas.users import UserProfile
from services import RecipeRecommender,RecipeService
from collections import defaultdict
from difflib import SequenceMatcher

from services.s3_service import upload_images_to_s3
from utils.form_parser import parse_recipe_form

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/", response_model=Recipe)
async def create_recipe(
    *,
    db: AsyncSession = Depends(get_async_db),
    recipe_in: RecipeCreate = Depends(parse_recipe_form),  # 폼 파서로 변경
    files: Optional[List[UploadFile]] = File(None),  # 이미지 파일 추가
    current_user: User = Depends(get_current_active_user)
):
    """Create new recipe with image uploads"""
    
    # 이미지 파일 확장자 검사
    if files:
        for file in files:
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif'}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file extension: {file_ext}"
                )
    
    # S3 업로드
    image_urls = await upload_images_to_s3(files) if files else []
    if files and not image_urls:
        raise HTTPException(status_code=500, detail="Failed to upload images to S3")
    
    # 첫 번째 이미지를 대표 이미지로 설정 (있는 경우)
    if image_urls:
        recipe_in.image_large = image_urls[0]
        recipe_in.image_small = image_urls[0]  # 필요한 경우 썸네일 URL을 다르게 설정할 수 있음
    
    # 요리 과정 이미지가 있다면 저장
    if len(image_urls) > 1:
        recipe_in.cooking_img = image_urls[1:]
    
    # 레시피 생성
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

@router.get("/my", response_model=List[Recipe])
async def get_my_recipes(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """현재 로그인한 사용자가
    생성한 레시피 목록 조회"""
    recipes = await crud_recipe.recipe.get_multi_by_owner(
        db=db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return recipes

@router.get("/search", response_model=List[Recipe])
async def search_recipes(
    query: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
    threshold: float = 0.4,  # 유사도 임계값 (기본값 0.4)
    limit: int = 10  # 최대 결과 수
):
    """레시피 이름 유사도 기반 검색"""
    # 모든 레시피 가져오기
    all_recipes = await crud_recipe.recipe.get_all_recipes(db)
    
    # 유사도 계산 및 정렬
    similar_recipes = []
    for recipe in all_recipes:
        # 유사도 계산 (case-insensitive)
        similarity = SequenceMatcher(None, query.lower(), recipe.name.lower()).ratio()
        if similarity >= threshold:
            similar_recipes.append((recipe, similarity))
    
    # 유사도에 따라 정렬하고 상위 결과 반환
    similar_recipes.sort(key=lambda x: x[1], reverse=True)
    top_recipes = [recipe for recipe, _ in similar_recipes[:limit]]
    
    return top_recipes

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
    if recipe.creator_id != current_user.id:
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
    if recipe.creator_id != current_user.id:
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