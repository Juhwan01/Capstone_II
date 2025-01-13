from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from crud.base import CRUDBase
from models.models import UserProfile
from schemas.users import UserProfileCreate, UserProfileUpdate

class CRUDUser(CRUDBase[UserProfile, UserProfileCreate, UserProfileUpdate]):
    async def get_profile(
        self, db: AsyncSession, *, user_id: int
    ) -> Optional[UserProfile]:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: UserProfileCreate, owner_id: int
    ) -> UserProfile:
        obj_in_data = obj_in.model_dump()  # .dict() 대신 model_dump() 사용
        db_obj = UserProfile(**obj_in_data, user_id=owner_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_ingredients(
        self, db: AsyncSession, *, user_id: int, ingredients: Dict[str, float]
    ) -> Optional[UserProfile]:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None

        current_ingredients = db_obj.owned_ingredients or {}
        for ingredient, amount in ingredients.items():
            current_ingredients[ingredient] = current_ingredients.get(ingredient, 0) + amount
        
        db_obj.owned_ingredients = current_ingredients
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_recipe_history(
        self, db: AsyncSession, *, user_id: int, recipe_id: int
    ) -> Optional[UserProfile]:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            return None

        history = db_obj.recipe_history or []
        if recipe_id not in history:
            history.append(recipe_id)
        db_obj.recipe_history = history
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

user = CRUDUser(UserProfile)