from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from crud.base import CRUDBase
from models.models import Recipe
from schemas import RecipeCreate, RecipeUpdate

class CRUDRecipe(CRUDBase[Recipe, RecipeCreate, RecipeUpdate]):
    async def get_recipe(self, db: AsyncSession, id: int) -> Optional[Recipe]:
        """레시피 단일 조회"""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all_recipes(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Recipe]:
        """레시피 목록 조회"""
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: RecipeCreate, owner_id: int
    ) -> Recipe:
        """소유자 정보와 함께 레시피 생성"""
        obj_in_data = obj_in.model_dump()
        db_obj = Recipe(**obj_in_data, creator_id=owner_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Recipe]:
        """소유자별 레시피 목록 조회"""
        result = await db.execute(
            select(Recipe)
            .filter(Recipe.creator_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_category(
        self, db: AsyncSession, *, category: str, skip: int = 0, limit: int = 100
    ) -> List[Recipe]:
        """카테고리별 레시피 목록 조회"""
        result = await db.execute(
            select(Recipe)
            .filter(Recipe.category == category)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_with_ingredients(
        self, 
        db: AsyncSession, 
        id: int
    ) -> Optional[Recipe]:
        """재료 정보를 포함한 레시피 조회"""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

recipe = CRUDRecipe(Recipe)