from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from crud.base import CRUDBase
from models.models import Recipe
from schemas.recipes import RecipeCreate, RecipeUpdate

class CRUDRecipe(CRUDBase[Recipe, RecipeCreate, RecipeUpdate]):
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: RecipeCreate, owner_id: int
    ) -> Recipe:
        obj_in_data = obj_in.model_dump()  # .dict() 대신 model_dump() 사용
        db_obj = Recipe(**obj_in_data, created_by=owner_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi_by_owner(
        self, db: AsyncSession, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Recipe]:
        result = await db.execute(
            select(Recipe)
            .where(Recipe.created_by == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

recipe = CRUDRecipe(Recipe)