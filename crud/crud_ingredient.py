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
    async def create_multiple_ingredients(self, ingredients: List[IngredientCreate], user_id: int):
        """ 여러 개의 재료를 한 번에 등록 """
        new_ingredients = []
        for ingredient in ingredients:
            db_ingredient = Ingredient(
                name=ingredient.name,
                category=ingredient.category,
                expiry_date=ingredient.expiry_date,
                amount=ingredient.amount,
                user_id=user_id
            )
            new_ingredients.append(db_ingredient)
            self.db.add(db_ingredient)

        await self.db.commit()  # 한 번의 트랜잭션으로 커밋
        for ing in new_ingredients:
            await self.db.refresh(ing)  # 모든 등록된 재료 새로고침

        # 유저 프로필 업데이트
        user_request = await self.db.execute(select(UserProfile).filter_by(user_id=user_id))
        user = user_request.scalar_one_or_none()
        if user:
            if user.owned_ingredients is None:
                user.owned_ingredients = {}

            for ing in new_ingredients:
                user.owned_ingredients[str(ing.id)] = {
                    "name": ing.name,
                    "amount": ing.amount
                }
            
            flag_modified(user, "owned_ingredients")
            self.db.add(user)
            await self.db.commit()
        
        return new_ingredients
    
    
    async def delete_ingredient(self, ingredient_id: int, user_id: int):
        """ 단일 재료 삭제 """
        # 재료 조회
        ingredient_query = await self.db.execute(
            select(Ingredient).filter_by(id=ingredient_id, user_id=user_id)
        )
        ingredient = ingredient_query.scalar_one_or_none()

        if not ingredient:
            return {"error": "Ingredient not found or unauthorized"}

        # 삭제
        await self.db.delete(ingredient)
        await self.db.commit()

        # 유저 프로필 업데이트 (재료 목록에서 제거)
        user_request = await self.db.execute(select(UserProfile).filter_by(user_id=user_id))
        user = user_request.scalar_one_or_none()

        if user and user.owned_ingredients:
            user.owned_ingredients.pop(str(ingredient_id), None)
            flag_modified(user, "owned_ingredients")
            self.db.add(user)
            await self.db.commit()

        return {"message": "Ingredient deleted successfully"}

    async def delete_multiple_ingredients(self, ingredient_ids: list, user_id: int):
        """ 여러 개의 재료 삭제 """
        # 해당 user_id의 식재료 가져오기
        ingredients_query = await self.db.execute(
            select(Ingredient).filter(Ingredient.id.in_(ingredient_ids), Ingredient.user_id == user_id)
        )
        ingredients = ingredients_query.scalars().all()

        if not ingredients:
            return {"error": "No matching ingredients found or unauthorized"}

        # 삭제 수행
        for ingredient in ingredients:
            await self.db.delete(ingredient)

        await self.db.commit()

        # 유저 프로필 업데이트
        user_request = await self.db.execute(select(UserProfile).filter_by(user_id=user_id))
        user = user_request.scalar_one_or_none()

        if user and user.owned_ingredients:
            for ing_id in ingredient_ids:
                user.owned_ingredients.pop(str(ing_id), None)

            flag_modified(user, "owned_ingredients")
            self.db.add(user)
            await self.db.commit()

        return {"message": f"{len(ingredients)} ingredients deleted successfully"}

    async def update_ingredient(self, ingredient_id: int, ingredient_data: IngredientUpdate, user_id: int):
            """ 특정 재료 업데이트 """
            # 재료 조회
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

            # 유저 프로필 업데이트 (재료 정보 반영)
            user_request = await self.db.execute(select(UserProfile).filter_by(user_id=user_id))
            user = user_request.scalar_one_or_none()

            if user and user.owned_ingredients:
                if str(ingredient.id) in user.owned_ingredients:
                    user.owned_ingredients[str(ingredient.id)] = {
                        "name": ingredient.name,
                        "amount": ingredient.amount
                    }
                    flag_modified(user, "owned_ingredients")
                    self.db.add(user)
                    await self.db.commit()

            return ingredient


