from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import IngredientRequest, Ingredient, UserProfile
from datetime import datetime
from schemas.ingredient import IngredientCreate
from sqlalchemy.orm.attributes import flag_modified
import json

class CRUDIngredient:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ingredient(self, ingredient: IngredientCreate, user_id: int):
        db_ingredient = Ingredient(
            name=ingredient.name,
            category=ingredient.category,
            expiry_date=ingredient.expiry_date,
            amount=ingredient.amount,
            user_id=user_id
        )
        self.db.add(db_ingredient)
        await self.db.commit()
        await self.db.refresh(db_ingredient)
        user_request = await self.db.execute(select(UserProfile).filter_by(user_id=user_id))
        user = user_request.scalar_one_or_none()
        if user:
            if user.owned_ingredients is None:
                user.owned_ingredients = {}
            user.owned_ingredients[db_ingredient.id] = [db_ingredient.name, db_ingredient.amount]
            flag_modified(user, "owned_ingredients")
            self.db.add(user)
            await self.db.commit()
            print(user.owned_ingredients)
        return db_ingredient