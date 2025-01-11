from collections import defaultdict
from typing import List, Dict, Tuple
import random

class Recipe:
    def __init__(self, id: int, name: str, ingredients: Dict[str, float], 
                 difficulty: int, cooking_time: int):
        self.id = id
        self.name = name
        self.ingredients = ingredients  # 재료: 필요량
        self.difficulty = difficulty    # 1-5
        self.cooking_time = cooking_time  # 분 단위

class UserProfile:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.owned_ingredients = defaultdict(float)  # 재료: 수량
        self.cooking_skill = 3  # 1-5
        self.preferred_cooking_time = 30  # 분 단위
        self.recipe_history = []
        self.ratings = {}

    def add_ingredient(self, ingredient: str, amount: float = 1.0):
        self.owned_ingredients[ingredient] += amount

    def use_ingredients(self, recipe: Recipe) -> bool:
        # 재료가 충분한지 확인
        if not self.can_cook(recipe):
            return False
            
        # 레시피에 필요한 재료 소비
        for ingredient, amount in recipe.ingredients.items():
            self.owned_ingredients[ingredient] -= amount
            if self.owned_ingredients[ingredient] <= 0:
                del self.owned_ingredients[ingredient]
        return True

    def can_cook(self, recipe: Recipe) -> bool:
        return all(self.owned_ingredients.get(ing, 0) >= amt 
                  for ing, amt in recipe.ingredients.items())

class RecipeRecommender:
    def __init__(self):
        self.q_values = defaultdict(float)
        self.user_history = defaultdict(list)
        self.feedback_history = defaultdict(list)
        self.exploration_rate = 0.1
        
        # 테스트용 레시피 데이터
        self.recipes = {
            1: Recipe(1, "김치찌개", 
                     {"김치": 1.0, "돼지고기": 0.3, "두부": 1.0, "대파": 0.5}, 2, 30),
            2: Recipe(2, "된장찌개",
                     {"된장": 0.3, "두부": 1.0, "감자": 2.0, "대파": 0.5, "양파": 1.0}, 2, 25),
            3: Recipe(3, "비빔밥",
                     {"밥": 1.0, "당근": 0.3, "오이": 0.5, "고추장": 0.2, "계란": 1.0, "시금치": 0.3}, 3, 20),
            4: Recipe(4, "불고기",
                     {"쇠고기": 0.5, "양파": 1.0, "당근": 0.5, "대파": 0.3}, 3, 40),
            5: Recipe(5, "떡볶이",
                     {"떡": 2.0, "고추장": 0.3, "어묵": 2.0, "대파": 0.3}, 1, 15),
        }

    def calculate_ingredient_match_score(self, recipe: Recipe, user_profile: UserProfile) -> float:
        available_ingredients = set(user_profile.owned_ingredients.keys())
        required_ingredients = set(recipe.ingredients.keys())
        
        matching_count = len(available_ingredients.intersection(required_ingredients))
        total_count = len(required_ingredients)
        
        return matching_count / total_count

    def calculate_recipe_score(self, recipe: Recipe, user_profile: UserProfile) -> float:
        # 만약 요리할 수 없는 레시피라면 낮은 점수 반환
        if not user_profile.can_cook(recipe):
            return 0.1
            
        ingredient_score = self.calculate_ingredient_match_score(recipe, user_profile)
        difficulty_match = 1 - abs(recipe.difficulty - user_profile.cooking_skill) / 4
        time_match = 1 - abs(recipe.cooking_time - user_profile.preferred_cooking_time) / 60
        q_value = self.q_values.get((user_profile.user_id, recipe.id), 0)
        
        return (ingredient_score * 0.4 +
                difficulty_match * 0.2 +
                time_match * 0.1 +
                q_value * 0.3)

    def get_recommendations(self, user_profile: UserProfile) -> List[Recipe]:
        available_recipes = list(self.recipes.values())
        recommendations = []
        
        recipe_scores = [(recipe, self.calculate_recipe_score(recipe, user_profile))
                        for recipe in available_recipes]
        recipe_scores.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = [recipe for recipe, _ in recipe_scores[:3]]
        
        remaining_recipes = [r for r in available_recipes if r not in recommendations]
        if remaining_recipes:
            exploration_recipe = random.choice(remaining_recipes)
            recommendations.append(exploration_recipe)
        
        return recommendations

    def update_feedback(self, user_id: int, recipe_id: int, rating: float):
        current_q = self.q_values.get((user_id, recipe_id), 0)
        learning_rate = 0.1
        self.q_values[(user_id, recipe_id)] = current_q + learning_rate * (rating - current_q)
        
        self.user_history[user_id].append(recipe_id)
        self.feedback_history[user_id].append(rating)

def test_recommendation_system():
    user = UserProfile(1)
    # 초기 재료 추가
    initial_ingredients = {
        "김치": 2.0,
        "두부": 2.0,
        "대파": 1.0,
        "양파": 2.0
    }
    for ing, amt in initial_ingredients.items():
        user.add_ingredient(ing, amt)

    recommender = RecipeRecommender()

    while True:
        print("\n=== 현재 보유 재료 ===")
        for ing, amt in user.owned_ingredients.items():
            print(f"{ing}: {amt:.1f}")
        
        recommendations = recommender.get_recommendations(user)
        
        print("\n=== 추천 레시피 ===")
        print("추천 (데이터 기반):")
        print("\n=== 추천 레시피 ===")
        for i, recipe in enumerate(recommendations, 1):
            q_value = recommender.q_values.get((user.user_id, recipe.id), 0)
            match_score = recommender.calculate_ingredient_match_score(recipe, user)
            
            # 탐험 추천 여부 표시
            is_exploration = i == 4
            print(f"{i}. {recipe.name} {'(탐험 추천)' if is_exploration else ''}")
            print(f"   - 필요 재료:", end=" ")
            for ing, amt in recipe.ingredients.items():
                print(f"{ing}({amt:.1f})", end=" ")
            print(f"\n   - 보유 재료 일치도: {match_score:.0%}")
            print(f"   - 난이도: {recipe.difficulty}/5")
            print(f"   - 조리시간: {recipe.cooking_time}분")
            print(f"   - Q값: {q_value:.2f}")
        
        choice = input("\n레시피를 선택하세요 (1-4, q로 종료, a로 재료추가): ")
        
        if choice.lower() == 'q':
            break
            
        if choice.lower() == 'a':
            new_ingredient = input("추가할 재료를 입력하세요: ")
            amount = float(input("수량을 입력하세요: "))
            user.add_ingredient(new_ingredient, amount)
            continue
            
        if choice.isdigit():
            choice = int(choice) - 1
            selected_recipe = recommendations[choice]
            
            if user.can_cook(selected_recipe):
                user.use_ingredients(selected_recipe)
                rating = float(input("평점을 입력하세요 (1-5): "))
                recommender.update_feedback(user.user_id, selected_recipe.id, rating)
                
                print("\n=== 선택 히스토리 ===")
                for recipe_id, rating in zip(recommender.user_history[user.user_id],
                                          recommender.feedback_history[user.user_id]):
                    print(f"{recommender.recipes[recipe_id].name}: {rating}점")
            else:
                print("재료가 부족합니다!")

if __name__ == "__main__":
    test_recommendation_system()