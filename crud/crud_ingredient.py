from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import IngredientRequest, Ingredient, UserProfile
from datetime import datetime
from schemas.ingredient import IngredientCreate, IngredientUpdate
from sqlalchemy.orm.attributes import flag_modified
from typing import List
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
        return db_ingredient

    async def create_multiple_ingredients(self, ingredients: List[IngredientCreate], user_id: int):
        new_ingredients = [
            Ingredient(
                name=ingredient.name,
                category=ingredient.category,
                expiry_date=ingredient.expiry_date,
                amount=ingredient.amount,
                user_id=user_id
            ) for ingredient in ingredients
        ]
        
        self.db.add_all(new_ingredients)
        await self.db.commit()
        
        for ing in new_ingredients:
            await self.db.refresh(ing)
        
        return new_ingredients

    async def delete_ingredient(self, ingredient_id: int, user_id: int):
        ingredient_query = await self.db.execute(
            select(Ingredient).filter_by(id=ingredient_id, user_id=user_id)
        )
        ingredient = ingredient_query.scalar_one_or_none()

        if not ingredient:
            return {"error": "Ingredient not found or unauthorized"}

        await self.db.delete(ingredient)
        await self.db.commit()

        return {"message": "Ingredient deleted successfully"}

    async def delete_multiple_ingredients(self, ingredient_ids: list, user_id: int):
        ingredients_query = await self.db.execute(
            select(Ingredient).filter(Ingredient.id.in_(ingredient_ids), Ingredient.user_id == user_id)
        )
        ingredients = ingredients_query.scalars().all()

        if not ingredients:
            return {"error": "No matching ingredients found or unauthorized"}

        for ingredient in ingredients:
            await self.db.delete(ingredient)

        await self.db.commit()

        return {"message": f"{len(ingredients)} ingredients deleted successfully"}

    async def update_ingredient(self, ingredient_id: int, ingredient_data: IngredientUpdate, user_id: int):
        ingredient_query = await self.db.execute(
            select(Ingredient).filter_by(id=ingredient_id, user_id=user_id)
        )
        ingredient = ingredient_query.scalar_one_or_none()

        if not ingredient:
            return {"error": "Ingredient not found or unauthorized"}

        # 변경 사항 반영
        if ingredient_data.name is not None:
            ingredient.name = ingredient_data.name
        if ingredient_data.category is not None:
            ingredient.category = ingredient_data.category
        if ingredient_data.expiry_date is not None:
            ingredient.expiry_date = ingredient_data.expiry_date
        if ingredient_data.amount is not None:
            ingredient.amount = ingredient_data.amount

        await self.db.commit()
        await self.db.refresh(ingredient)

        return ingredient