import random
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import math

@dataclass
class Recipe:
    id: int
    name: str
    required_ingredients: List[str]
    optional_ingredients: List[str]
    difficulty: int  # 1-5
    cooking_time: int  # minutes
    category: str

@dataclass
class UserState:
    user_id: int
    cooking_level: int  # 1-5
    preferred_categories: List[str]
    recent_recipes: List[int]  # 최근 조리한 레시피 ID
    favorite_ingredients: List[str]
    location: Tuple[float, float]  # (latitude, longitude)

class RecipeRecommendationSystem:
    def __init__(self):
        self.exploration_rate = 0.1  # 10% 탐험
        self.q_values = {}  # (user_id, recipe_id) -> q_value
        self.rewards_history = {}  # (user_id, recipe_id) -> [rewards]
        
    def get_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """두 지점 간의 거리 계산 (km)"""
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        R = 6371  # 지구 반경 (km)
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def find_recipes_with_owned_ingredients(
        self, 
        user_ingredients: Set[str], 
        available_recipes: List[Recipe]
    ) -> List[Recipe]:
        """보유 재료로만 만들 수 있는 레시피 찾기"""
        full_matches = []
        for recipe in available_recipes:
            required_ingredients = set(recipe.required_ingredients)
            if required_ingredients.issubset(user_ingredients):
                full_matches.append(recipe)
        return full_matches

    def find_recipes_with_few_missing(
        self, 
        user_ingredients: Set[str], 
        available_recipes: List[Recipe], 
        max_missing: int = 2
    ) -> List[Tuple[Recipe, int]]:
        """최대 N개 재료 추가 구매로 만들 수 있는 레시피 찾기"""
        partial_matches = []
        for recipe in available_recipes:
            required_ingredients = set(recipe.required_ingredients)
            missing = required_ingredients - user_ingredients
            if 0 < len(missing) <= max_missing:
                partial_matches.append((recipe, len(missing)))
        return partial_matches

    def find_tradeable_ingredients(
        self, 
        user_location: Tuple[float, float],
        needed_ingredients: Set[str],
        available_trades: Dict[str, List[Tuple[float, float]]],
        max_distance: float = 3.0
    ) -> Dict[str, List[Tuple[float, float]]]:
        """교환 가능한 재료 찾기"""
        tradeable = {}
        for ingredient in needed_ingredients:
            if ingredient in available_trades:
                locations = available_trades[ingredient]
                nearby_locations = [
                    loc for loc in locations
                    if self.get_distance(user_location, loc) <= max_distance
                ]
                if nearby_locations:
                    tradeable[ingredient] = nearby_locations
        return tradeable

    def calculate_recipe_score(
        self,
        recipe: Recipe,
        user_state: UserState,
        match_info: Dict
    ) -> float:
        """레시피 점수 계산"""
        base_score = 0.0
        
        # 1. 재료 매칭 점수 (40%)
        ingredient_score = 0.0
        if match_info['match_type'] == 'full':
            ingredient_score = 1.0
        elif match_info['match_type'] == 'partial':
            ingredient_score = 1.0 - (match_info['missing_count'] * 0.2)  # 부족한 재료당 20% 감점
        elif match_info['match_type'] == 'tradeable':
            ingredient_score = 0.8  # 교환 가능한 경우 기본 80%
        base_score += ingredient_score * 0.4

        # 2. 난이도 적합성 (20%)
        difficulty_diff = abs(recipe.difficulty - user_state.cooking_level)
        difficulty_score = 1.0 - (difficulty_diff * 0.2)
        base_score += max(0, difficulty_score) * 0.2

        # 3. 선호도 점수 (20%)
        preference_score = 0.0
        if recipe.category in user_state.preferred_categories:
            preference_score = 1.0
        base_score += preference_score * 0.2

        # 4. 다양성 점수 (20%)
        diversity_score = 1.0
        if recipe.id in user_state.recent_recipes:
            diversity_score = 0.5  # 최근에 만든 요리는 점수 감소
        base_score += diversity_score * 0.2

        return base_score

    def get_q_value(self, user_id: int, recipe_id: int) -> float:
        """Q값 조회"""
        return self.q_values.get((user_id, recipe_id), 0.0)

    def update_q_value(
        self, 
        user_id: int, 
        recipe_id: int, 
        reward: float, 
        learning_rate: float = 0.1
    ):
        """Q값 업데이트"""
        current_q = self.get_q_value(user_id, recipe_id)
        self.q_values[(user_id, recipe_id)] = current_q + learning_rate * (reward - current_q)

    def recommend_recipes(
        self,
        user_state: UserState,
        user_ingredients: Set[str],
        available_recipes: List[Recipe],
        available_trades: Dict[str, List[Tuple[float, float]]]
    ) -> Dict[str, List[Recipe]]:
        """최종 레시피 추천"""
        # 1. 가능한 모든 레시피 찾기
        full_matches = self.find_recipes_with_owned_ingredients(user_ingredients, available_recipes)
        partial_matches = self.find_recipes_with_few_missing(user_ingredients, available_recipes)
        
        all_possible_recipes = []
        
        # 완전 매칭 레시피 추가
        for recipe in full_matches:
            all_possible_recipes.append({
                'recipe': recipe,
                'match_type': 'full',
                'missing_count': 0,
                'score': self.calculate_recipe_score(
                    recipe, 
                    user_state, 
                    {'match_type': 'full', 'missing_count': 0}
                )
            })
        
        # 부분 매칭 레시피 추가
        for recipe, missing_count in partial_matches:
            # 부족한 재료의 교환 가능 여부 확인
            missing_ingredients = set(recipe.required_ingredients) - user_ingredients
            tradeable = self.find_tradeable_ingredients(
                user_state.location,
                missing_ingredients,
                available_trades
            )
            
            match_type = 'tradeable' if tradeable else 'partial'
            all_possible_recipes.append({
                'recipe': recipe,
                'match_type': match_type,
                'missing_count': missing_count,
                'tradeable_ingredients': tradeable if tradeable else {},
                'score': self.calculate_recipe_score(
                    recipe,
                    user_state,
                    {'match_type': match_type, 'missing_count': missing_count}
                )
            })

        # 2. Q값 적용
        for recipe_info in all_possible_recipes:
            q_value = self.get_q_value(user_state.user_id, recipe_info['recipe'].id)
            recipe_info['final_score'] = recipe_info['score'] * 0.7 + q_value * 0.3

        # 3. 점수순 정렬
        all_possible_recipes.sort(key=lambda x: x['final_score'], reverse=True)

        # 4. 추천 & 탐험 레시피 선택
        recommendations = {'recommended': [], 'exploration': None}
        
        # 상위 3개 추천 레시피 선택
        recommendations['recommended'] = [
            recipe_info['recipe'] for recipe_info in all_possible_recipes[:3]
        ]

        # 탐험 레시피 선택 (남은 레시피 중에서 랜덤 선택)
        if len(all_possible_recipes) > 3:
            exploration_candidate = random.choice(all_possible_recipes[3:])
            recommendations['exploration'] = exploration_candidate['recipe']

        return recommendations

    def process_feedback(
        self,
        user_id: int,
        recipe_id: int,
        satisfaction: int,  # 1-5
        difficulty_rating: int,  # 1-5
        would_cook_again: bool
    ):
        """사용자 피드백 처리"""
        # 보상 계산
        reward = (satisfaction / 5.0) * 0.5  # 만족도 (50%)
        reward += (1 - abs(difficulty_rating - 3) / 2) * 0.3  # 난이도 적절성 (30%)
        reward += (1.0 if would_cook_again else 0.0) * 0.2  # 재조리 의향 (20%)

        # Q값 업데이트
        self.update_q_value(user_id, recipe_id, reward)

        # 이력 저장
        if (user_id, recipe_id) not in self.rewards_history:
            self.rewards_history[(user_id, recipe_id)] = []
        self.rewards_history[(user_id, recipe_id)].append(reward)

# 테스트를 위한 샘플 데이터
def create_sample_data():
    # 샘플 레시피
    recipes = [
        Recipe(
            id=1,
            name="김치찌개",
            required_ingredients=["김치", "돼지고기", "두부", "파"],
            optional_ingredients=["고춧가루", "다진마늘"],
            difficulty=2,
            cooking_time=30,
            category="한식"
        ),
        Recipe(
            id=2,
            name="파스타",
            required_ingredients=["면", "올리브오일", "마늘", "파마산치즈"],
            optional_ingredients=["바질", "페퍼론치노"],
            difficulty=3,
            cooking_time=20,
            category="양식"
        ),
        Recipe(
            id=3,
            name="계란말이",
            required_ingredients=["계란", "파", "당근"],
            optional_ingredients=["맛술", "설탕"],
            difficulty=1,
            cooking_time=15,
            category="한식"
        ),
    ]

    # 샘플 유저
    user_state = UserState(
        user_id=1,
        cooking_level=2,
        preferred_categories=["한식", "양식"],
        recent_recipes=[2],  # 최근에 파스타를 만듦
        favorite_ingredients=["김치", "계란"],
        location=(37.5665, 126.9780)  # 서울시청
    )

    # 보유 재료
    user_ingredients = {
        "김치", "두부", "파", "계란", "당근"
    }

    # 주변 교환 가능한 재료
    available_trades = {
        "돼지고기": [(37.5668, 126.9785)],  # 서울시청 근처
        "면": [(37.5660, 126.9775)],
        "올리브오일": [(37.5670, 126.9790)]
    }

    return recipes, user_state, user_ingredients, available_trades

def test_recommendation_system():
    # 시스템 초기화
    system = RecipeRecommendationSystem()
    
    # 샘플 데이터 생성
    recipes, user_state, user_ingredients, available_trades = create_sample_data()
    
    # 레시피 추천 받기
    recommendations = system.recommend_recipes(
        user_state,
        user_ingredients,
        recipes,
        available_trades
    )
    
    # 결과 출력
    print("\n=== 추천 레시피 ===")
    for i, recipe in enumerate(recommendations['recommended'], 1):
        print(f"\n{i}. {recipe.name}")
        print(f"   난이도: {recipe.difficulty}/5")
        print(f"   필요한 재료: {', '.join(recipe.required_ingredients)}")
        print(f"   선택 재료: {', '.join(recipe.optional_ingredients)}")
        print(f"   조리 시간: {recipe.cooking_time}분")
    
    if recommendations['exploration']:
        print(f"\n=== 이런 요리는 어떠세요? ===")
        recipe = recommendations['exploration']
        print(f"   {recipe.name}")
        print(f"   난이도: {recipe.difficulty}/5")
        print(f"   필요한 재료: {', '.join(recipe.required_ingredients)}")
        print(f"   조리 시간: {recipe.cooking_time}분")

    # 피드백 테스트
    print("\n=== 피드백 테스트 ===")
    system.process_feedback(
        user_id=1,
        recipe_id=1,
        satisfaction=4,  # 4/5 만족
        difficulty_rating=3,  # 난이도 적절
        would_cook_again=True
    )
    print("피드백 처리 완료")

if __name__ == "__main__":
    test_recommendation_system()