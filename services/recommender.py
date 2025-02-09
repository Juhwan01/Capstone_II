from typing import List, Dict
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Recipe, UserProfile, QValue
from schemas.recipes import Recipe as RecipeSchema
from schemas.users import UserProfile as UserProfileSchema
from schemas.users import RecommendationResponse

class RecipeRecommender:
    def calculate_ingredient_match_score(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> float:
        """재료 매칭 점수 계산 (기존 로직 유지)"""
        available_ingredients = set(user_profile.owned_ingredients.keys())
        required_ingredients = set(recipe.ingredients.keys())
        
        matching_count = len(available_ingredients.intersection(required_ingredients))
        total_count = len(required_ingredients)
        
        return matching_count / total_count if total_count > 0 else 0

    def can_cook(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> bool:
        """요리 가능 여부 확인 (기존 로직 유지)"""
        return all(
            user_profile.owned_ingredients.get(ing, 0) >= amt 
            for ing, amt in recipe.ingredients.items()
        )

    def calculate_nutrition_limits_score(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> float:
        """영양소 제한 기반 점수 계산"""
        scores = []
        
        # nutrition_limits가 없으면 1.0 반환
        if not user_profile.nutrition_limits:
            return 1.0
        
        limits = user_profile.nutrition_limits
        
        # 각 영양소별 제한 체크
        if recipe.calories and limits.max_calories:
            if recipe.calories > limits.max_calories:
                return 0.0  # 제한 초과시 즉시 0점 반환
            scores.append(1 - (recipe.calories / limits.max_calories))
        
        if recipe.carbs and limits.max_carbs:
            if float(recipe.carbs) > float(limits.max_carbs):
                return 0.0
            scores.append(1 - (float(recipe.carbs) / float(limits.max_carbs)))
        
        if recipe.protein and limits.max_protein:
            if float(recipe.protein) > float(limits.max_protein):
                return 0.0
            scores.append(1 - (float(recipe.protein) / float(limits.max_protein)))
        
        if recipe.fat and limits.max_fat:
            if float(recipe.fat) > float(limits.max_fat):
                return 0.0
            scores.append(1 - (float(recipe.fat) / float(limits.max_fat)))
        
        if recipe.sodium and limits.max_sodium:
            if float(recipe.sodium) > float(limits.max_sodium):
                return 0.0
            scores.append(1 - (float(recipe.sodium) / float(limits.max_sodium)))
        
        return sum(scores) / len(scores) if scores else 1.0

    def calculate_recipe_score(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema, q_value: float
    ) -> float:
        """전체 레시피 점수 계산"""
        # 영양소 제한 체크
        nutrition_limits_score = self.calculate_nutrition_limits_score(recipe, user_profile)
        if nutrition_limits_score == 0.0:
            return 0.0  # 영양소 제한 초과시 추천하지 않음
            
        ingredient_score = self.calculate_ingredient_match_score(recipe, user_profile)
        
        return (
            ingredient_score * 0.4 +           # 재료 매칭
            nutrition_limits_score * 0.3 +     # 영양소 제한 준수
            q_value * 0.3                      # 학습된 선호도
        )

    async def get_recommendations(
        self, db: AsyncSession, user_id: int
    ) -> List[RecommendationResponse]:
        """추천 레시피 조회 (기존 로직 유지)"""
        # Get user profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        user_profile = result.scalar_one_or_none()
        if not user_profile:
            return []

        # Get all recipes
        result = await db.execute(select(Recipe))
        recipes = result.scalars().all()

        # Get Q-values
        result = await db.execute(
            select(QValue).where(QValue.user_id == user_id)
        )
        q_values = {qv.recipe_id: qv.value for qv in result.scalars().all()}

        # Calculate scores
        recipe_scores = [
            (
                recipe,
                self.calculate_recipe_score(
                    RecipeSchema.model_validate(recipe),
                    UserProfileSchema.model_validate(user_profile),
                    q_values.get(recipe.id, 0)
                )
            )
            for recipe in recipes
        ]

        # Sort by score
        recipe_scores.sort(key=lambda x: x[1], reverse=True)
        recommendations = recipe_scores[:3]

        # Add exploration recipe
        remaining_recipes = [r for r, _ in recipe_scores[3:]]
        if remaining_recipes:
            exploration_recipe = random.choice(remaining_recipes)
            recommendations.append((exploration_recipe, 0))

        return [
            RecommendationResponse(
                recipe=RecipeSchema.model_validate(recipe),
                score=score,
                is_exploration=(i == 3)
            )
            for i, (recipe, score) in enumerate(recommendations)
        ]

    async def update_q_value(
        self,
        db: AsyncSession,
        user_id: int,
        recipe_id: int,
        reward: float,
        learning_rate: float = 0.1
    ) -> None:
        """Q-value 업데이트 (기존 로직 유지)"""
        result = await db.execute(
            select(QValue).where(
                QValue.user_id == user_id,
                QValue.recipe_id == recipe_id
            )
        )
        q_value = result.scalar_one_or_none()
        
        if q_value:
            q_value.value = (1 - learning_rate) * q_value.value + learning_rate * reward
        else:
            q_value = QValue(
                user_id=user_id,
                recipe_id=recipe_id,
                value=reward * learning_rate
            )
            db.add(q_value)
        
        await db.commit()