from typing import List, Dict
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Recipe, UserProfile, QValue
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
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> float:
        """텍스트 유사도 기반 재료 매칭 점수 계산"""
        try:
            return self.ingredient_mapper.calculate_ingredient_match_score(
                recipe.ingredients, 
                user_profile.owned_ingredients
            )
        except Exception as e:
            print(f"재료 매칭 점수 계산 오류: {e}")
            return 0.0

    def can_cook(
        self, recipe: RecipeSchema, user_profile: UserProfileSchema
    ) -> bool:
        """텍스트 유사도 기반 요리 가능 여부 확인"""
        try:
            return self.ingredient_mapper.can_cook(
                recipe.ingredients,
                user_profile.owned_ingredients
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
        self, recipe: RecipeSchema, user_profile: UserProfileSchema, q_value: float
    ) -> float:
        """전체 레시피 점수 계산"""
        # 초기 사용자일 경우의 처리
        is_new_user = not user_profile.recipe_history or len(user_profile.recipe_history) == 0
        
        # 영양소 제한 체크
        nutrition_limits_score = self.calculate_nutrition_limits_score(recipe, user_profile)
        if nutrition_limits_score == 0.0:
            return 0.0  # 영양소 제한 초과시 추천하지 않음
            
        # 재료 매칭 점수
        ingredient_score = self.calculate_ingredient_match_score(recipe, user_profile)
        
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
        """추천 레시피 조회"""
        # Get user profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        user_profile_db = result.scalar_one_or_none()
        if not user_profile_db:
            return []

        try:
            # 필요한 속성 직접 추출
            owned_ingredients_raw = user_profile_db.owned_ingredients
            
            # 형식에 맞게 변환: 리스트 -> 딕셔너리
            owned_ingredients = {}
            if isinstance(owned_ingredients_raw, list):
                for item in owned_ingredients_raw:
                    if isinstance(item, dict) and 'name' in item and 'amount' in item:
                        owned_ingredients[item['name']] = item['amount']
            else:
                owned_ingredients = owned_ingredients_raw
            
            # 영양소 제한 
            nutrition_limits = getattr(user_profile_db, 'nutrition_limits', {}) or {}
            
            # 레시피 히스토리
            recipe_history = getattr(user_profile_db, 'recipe_history', []) or []

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
                    # 영양소 매칭 정보
                    nutrition_match = {}
                    if nutrition_limits:
                        if getattr(recipe, 'calories', None) and nutrition_limits.get('max_calories'):
                            nutrition_match['calories'] = recipe.calories / nutrition_limits['max_calories']
                        if getattr(recipe, 'carbs', None) and nutrition_limits.get('max_carbs'):
                            nutrition_match['carbs'] = float(recipe.carbs) / float(nutrition_limits['max_carbs'])
                        if getattr(recipe, 'protein', None) and nutrition_limits.get('max_protein'):
                            nutrition_match['protein'] = float(recipe.protein) / float(nutrition_limits['max_protein'])
                        if getattr(recipe, 'fat', None) and nutrition_limits.get('max_fat'):
                            nutrition_match['fat'] = float(recipe.fat) / float(limits['max_fat'])
                        if getattr(recipe, 'sodium', None) and nutrition_limits.get('max_sodium'):
                            nutrition_match['sodium'] = float(recipe.sodium) / float(nutrition_limits['max_sodium'])
                    
                    # 재료 매칭 점수 계산
                    ingredient_score = self.ingredient_mapper.calculate_ingredient_match_score(
                        recipe.ingredients, 
                        owned_ingredients
                    )
                    
                    # 영양소 점수 계산
                    nutrition_score = 1.0
                    if nutrition_limits:
                        nutrition_scores = []
                        if getattr(recipe, 'calories', None) and nutrition_limits.get('max_calories'):
                            if recipe.calories > nutrition_limits['max_calories']:
                                nutrition_score = 0.0
                                break
                            nutrition_scores.append(1 - (recipe.calories / nutrition_limits['max_calories']))
                        if nutrition_score > 0 and getattr(recipe, 'carbs', None) and nutrition_limits.get('max_carbs'):
                            if float(recipe.carbs) > float(nutrition_limits['max_carbs']):
                                nutrition_score = 0.0
                                break
                            nutrition_scores.append(1 - (float(recipe.carbs) / float(nutrition_limits['max_carbs'])))
                        # 나머지 영양소도 비슷하게 처리
                        if nutrition_scores:
                            nutrition_score = sum(nutrition_scores) / len(nutrition_scores)
                    
                    # 초기 사용자 여부 확인
                    is_new_user = len(recipe_history) == 0
                    
                    # 최종 점수 계산
                    if is_new_user:
                        diversity_score = random.uniform(0.3, 1.0)
                        score = (
                            ingredient_score * 0.4 +
                            nutrition_score * 0.3 +
                            diversity_score * 0.3
                        )
                    else:
                        score = (
                            ingredient_score * 0.4 +
                            nutrition_score * 0.3 +
                            q_values.get(recipe.id, 0) * 0.3
                        )
                    
                    recipe_scores.append((recipe, score, nutrition_match))
                except Exception as e:
                    print(f"레시피 점수 계산 오류 ({getattr(recipe, 'name', 'unknown')}): {e}")
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
            responses = []
            for i, (recipe, score, nutrition_match) in enumerate(recommendations):
                try:
                    recipe_dict = {
                        "id": recipe.id,
                        "name": recipe.name,
                        "category": getattr(recipe, 'category', None),
                        "calories": getattr(recipe, 'calories', None),
                        "carbs": getattr(recipe, 'carbs', None),
                        "protein": getattr(recipe, 'protein', None),
                        "fat": getattr(recipe, 'fat', None),
                        "sodium": getattr(recipe, 'sodium', None),
                        "image_small": getattr(recipe, 'image_small', None),
                        "image_large": getattr(recipe, 'image_large', None),
                        "ingredients": recipe.ingredients,
                        "instructions": getattr(recipe, 'instructions', {}),
                        "cooking_img": getattr(recipe, 'cooking_img', {}),
                        "creator_id": getattr(recipe, 'creator_id', None)
                    }
                    responses.append(
                        RecommendationResponse(
                            recipe=recipe_dict,
                            score=score,
                            is_exploration=(i == 3),
                            nutrition_match=nutrition_match
                        )
                    )
                except Exception as e:
                    print(f"레시피 응답 생성 오류: {e}")
                    continue
                    
            return responses
        
        except Exception as e:
            print(f"추천 시스템 오류: {e}")
            # 스택 트레이스 출력 (디버깅 목적)
            import traceback
            traceback.print_exc()
            return []

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