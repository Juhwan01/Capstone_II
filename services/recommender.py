from typing import List, Dict
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Recipe, UserProfile, QValue, Ingredient
from schemas.recipes import Recipe as RecipeSchema
from schemas.users import UserProfile as UserProfileSchema
from schemas.users import RecommendationResponse

# 텍스트 유사도 기반 재료 매퍼 import
from utils.ingredient_mapper import IngredientMapper

class RecipeRecommender:
    def __init__(self):
        # 재료 매퍼 초기화 (표준 재료 파일 경로 및 임계값 설정)
        self.ingredient_mapper = IngredientMapper(
            standard_ingredients_file="data/standard_ingredients.json",
            threshold=0.6
        )

    def calculate_ingredient_match_score(
        self, recipe: RecipeSchema, user_ingredients: Dict[str, float]
    ) -> float:
        """텍스트 유사도 기반 재료 매칭 점수 계산"""
        try:
            return self.ingredient_mapper.calculate_ingredient_match_score(
                recipe.ingredients, 
                user_ingredients
            )
        except Exception as e:
            print(f"재료 매칭 점수 계산 오류: {e}")
            return 0.0

    def can_cook(
        self, recipe: RecipeSchema, user_ingredients: Dict[str, float]
    ) -> bool:
        """텍스트 유사도 기반 요리 가능 여부 확인"""
        try:
            return self.ingredient_mapper.can_cook(
                recipe.ingredients,
                user_ingredients
            )
        except Exception as e:
            print(f"요리 가능 여부 확인 오류: {e}")
            return False

    def calculate_nutrition_limits_score(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> float:
        """영양소 제한 기반 점수 계산"""
        scores = []
        
        # nutrition_limits가 없으면 1.0 반환
        if not hasattr(user_profile, 'nutrition_limits') or not user_profile.nutrition_limits:
            return 1.0
        
        limits = user_profile.nutrition_limits
        
        # 각 영양소별 제한 체크
        if recipe.calories and limits.get('max_calories'):
            if recipe.calories > limits['max_calories']:
                return 0.0  # 제한 초과시 즉시 0점 반환
            scores.append(1 - (recipe.calories / limits['max_calories']))
        
        if recipe.carbs and limits.get('max_carbs'):
            if float(recipe.carbs) > float(limits['max_carbs']):
                return 0.0
            scores.append(1 - (float(recipe.carbs) / float(limits['max_carbs'])))
        
        if recipe.protein and limits.get('max_protein'):
            if float(recipe.protein) > float(limits['max_protein']):
                return 0.0
            scores.append(1 - (float(recipe.protein) / float(limits['max_protein'])))
        
        if recipe.fat and limits.get('max_fat'):
            if float(recipe.fat) > float(limits['max_fat']):
                return 0.0
            scores.append(1 - (float(recipe.fat) / float(limits['max_fat'])))
        
        if recipe.sodium and limits.get('max_sodium'):
            if float(recipe.sodium) > float(limits['max_sodium']):
                return 0.0
            scores.append(1 - (float(recipe.sodium) / float(limits['max_sodium'])))
        
        return sum(scores) / len(scores) if scores else 1.0

    def calculate_recipe_score(
        self, recipe: RecipeSchema, user_ingredients: Dict[str, float], 
        user_profile: UserProfileSchema, q_value: float
    ) -> float:
        """전체 레시피 점수 계산"""
        # 초기 사용자일 경우의 처리
        is_new_user = not user_profile.recipe_history or len(user_profile.recipe_history) == 0
        
        # 영양소 제한 체크
        nutrition_limits_score = self.calculate_nutrition_limits_score(recipe, user_profile)
        if nutrition_limits_score == 0.0:
            return 0.0  # 영양소 제한 초과시 추천하지 않음
            
        # 재료 매칭 점수
        ingredient_score = self.calculate_ingredient_match_score(recipe, user_ingredients)
        
        # 새로운 사용자의 경우 다양성을 위한 랜덤 요소 추가
        if is_new_user:
            diversity_score = random.uniform(0.3, 1.0)
            return (
                ingredient_score * 0.4 +           # 재료 매칭 (40%)
                nutrition_limits_score * 0.3 +     # 영양소 제한 준수 (30%)
                diversity_score * 0.3              # 다양성 (30%)
            )
        else:
            return (
                ingredient_score * 0.4 +           # 재료 매칭 (40%)
                nutrition_limits_score * 0.3 +     # 영양소 제한 준수 (30%)
                q_value * 0.3                      # 학습된 선호도 (30%)
            )

    async def get_recommendations(
    self, db: AsyncSession, user_id: int
    ) -> List[RecommendationResponse]:
        # 기존 코드와 유사하지만, 재료 매칭 로직 개선
        ingredient_result = await db.execute(
            select(Ingredient).where(Ingredient.user_id == user_id)
        )
        user_ingredients = {
            ingredient.name: ingredient.amount 
            for ingredient in ingredient_result.scalars().all()
        }

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
        recipe_scores = []
        for recipe in recipes:
            try:
                # 재료 매칭 정보 계산
                mapped_recipe = self.ingredient_mapper.map_ingredients(recipe.ingredients)
                mapped_owned = self.ingredient_mapper.map_ingredients(user_ingredients)
                
                # 영양소 매칭 정보
                nutrition_match = {}
                if hasattr(user_profile, 'nutrition_limits') and user_profile.nutrition_limits:
                    limits = user_profile.nutrition_limits
                    if recipe.calories and limits.get('max_calories'):
                        nutrition_match['calories'] = recipe.calories / limits['max_calories']
                    if recipe.carbs and limits.get('max_carbs'):
                        nutrition_match['carbs'] = float(recipe.carbs) / float(limits['max_carbs'])
                    if recipe.protein and limits.get('max_protein'):
                        nutrition_match['protein'] = float(recipe.protein) / float(limits['max_protein'])
                    if recipe.fat and limits.get('max_fat'):
                        nutrition_match['fat'] = float(recipe.fat) / float(limits['max_fat'])
                    if recipe.sodium and limits.get('max_sodium'):
                        nutrition_match['sodium'] = float(recipe.sodium) / float(limits['max_sodium'])
                
                # 레시피 점수 계산
                score = self.calculate_recipe_score(
                    RecipeSchema.model_validate(recipe),
                    user_ingredients,  # 변경된 부분
                    UserProfileSchema.model_validate(user_profile),
                    q_values.get(recipe.id, 0)
                )
                
                recipe_scores.append((recipe, score, nutrition_match))
            except Exception as e:
                print(f"레시피 점수 계산 오류 ({recipe.name}): {e}")
                continue

        # Sort by score
        recipe_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 추천 결과 설정 (상위 3개)
        recommendations = recipe_scores[:3]
        
        # Add exploration recipe (남은 레시피 중 랜덤 선택)
        remaining_recipes = [(r, s, n) for r, s, n in recipe_scores[3:] if s > 0]
        if remaining_recipes:
            exploration_recipe = random.choice(remaining_recipes)
            recommendations.append((exploration_recipe[0], 0, exploration_recipe[2]))
        
        # Create response
        return [
            RecommendationResponse(
                recipe=RecipeSchema.model_validate(recipe),
                score=score,
                is_exploration=(i == 3),
                nutrition_match=nutrition_match
            )
            for i, (recipe, score, nutrition_match) in enumerate(recommendations)
        ]

    async def update_q_value(
        self,
        db: AsyncSession,
        user_id: int,
        recipe_id: int,
        reward: float,
        learning_rate: float = 0.1
    ) -> None:
        """Q-value 업데이트"""
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