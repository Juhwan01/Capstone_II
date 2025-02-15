from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from crud.base import CRUDBase
from models.models import UserProfile
from schemas.users import UserProfileCreate, UserProfileUpdate
from sqlalchemy import inspect
from sqlalchemy.orm.attributes import flag_modified

class CRUDUserProfile(CRUDBase[UserProfile, UserProfileCreate, UserProfileUpdate]):
    async def get_profile(
        self, 
        db: AsyncSession, 
        user_id: int
    ) -> Optional[UserProfile]:
        """사용자 프로필 조회"""
        result = await db.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_ingredients(
        self, 
        db: AsyncSession, 
        profile: UserProfile, 
        ingredients_update: Dict[str, float]
    ) -> UserProfile:
        """재료 수량 업데이트"""
        for ingredient, amount in ingredients_update.items():
            profile.owned_ingredients[ingredient] = amount
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    async def update_recipe_history(
        self, 
        db: AsyncSession, 
        profile: UserProfile, 
        recipe_id: int
    ) -> UserProfile:
        """레시피 히스토리 업데이트"""
        if profile.recipe_history is None:
            profile.recipe_history = []
        
        # 새로운 리스트 생성 및 할당
        updated_history = list(profile.recipe_history)
        if recipe_id not in updated_history:
            updated_history.append(recipe_id)
            profile.recipe_history = updated_history
            
            # flag_modified 사용하여 변경 감지
            flag_modified(profile, "recipe_history")
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    async def update_rating(
        self, 
        db: AsyncSession, 
        profile: UserProfile, 
        recipe_id: int, 
        rating: float
    ) -> UserProfile:
        """레시피 평가 업데이트"""
        if profile.ratings is None:
            profile.ratings = {}
        
        # 새로운 딕셔너리 생성 및 할당
        updated_ratings = dict(profile.ratings)
        updated_ratings[str(recipe_id)] = rating
        profile.ratings = updated_ratings
        
        # flag_modified 직접 사용
        flag_modified(profile, "ratings")
        
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

user_profile = CRUDUserProfile(UserProfile)