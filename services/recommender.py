from typing import List, Dict
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Recipe, UserProfile, QValue
from schemas.recipes import Recipe as RecipeSchema
from schemas.users import UserProfile as UserProfileSchema
from schemas.users import RecommendationResponse

class RecipeRecommender:
    def calculate_ingredient_match_score(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> float:
        available_ingredients = set(user_profile.owned_ingredients.keys())
        required_ingredients = set(recipe.ingredients.keys())
        
        matching_count = len(available_ingredients.intersection(required_ingredients))
        total_count = len(required_ingredients)
        
        return matching_count / total_count if total_count > 0 else 0

    def can_cook(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> bool:
        return all(
            user_profile.owned_ingredients.get(ing, 0) >= amt 
            for ing, amt in recipe.ingredients.items()
        )

    def calculate_recipe_score(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema, q_value: float
    ) -> float:
        if not self.can_cook(recipe, user_profile):
            return 0.1
            
        ingredient_score = self.calculate_ingredient_match_score(
            recipe, user_profile
        )
        difficulty_match = 1 - abs(recipe.difficulty - user_profile.cooking_skill) / 4
        time_match = 1 - abs(
            recipe.cooking_time - user_profile.preferred_cooking_time
        ) / 60
        
        return (
            ingredient_score * 0.4 +
            difficulty_match * 0.2 +
            time_match * 0.1 +
            q_value * 0.3
        )

    async def get_recommendations(
        self, db: AsyncSession, user_id: int
    ) -> List[RecommendationResponse]:
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
                    RecipeSchema.model_validate(recipe),  # from_orm 대신 model_validate 사용
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

        # Create response
        return [
            RecommendationResponse(
                recipe=RecipeSchema.model_validate(recipe),
                score=score,
                is_exploration=(i == 3)
            )
            for i, (recipe, score) in enumerate(recommendations)
        ]

    # 기존 recommender.py의 RecipeRecommender 클래스에 추가
    async def update_q_value(
        self,
        db: AsyncSession,
        user_id: int,
        recipe_id: int,
        reward: float,
        learning_rate: float = 0.1
    ) -> None:
        """Update Q-value based on user feedback"""
        result = await db.execute(
            select(QValue).where(
                QValue.user_id == user_id,
                QValue.recipe_id == recipe_id
            )
        )
        q_value = result.scalar_one_or_none()
        
        if q_value:
            # Update existing Q-value
            q_value.value = (1 - learning_rate) * q_value.value + learning_rate * reward
        else:
            # Create new Q-value
            q_value = QValue(
                user_id=user_id,
                recipe_id=recipe_id,
                value=reward * learning_rate
            )
            db.add(q_value)
        
        await db.commit()