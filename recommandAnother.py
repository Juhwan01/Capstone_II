import random
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Set
import json
import math

class RecipeRecommender:
    def __init__(self):
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        
        # Exploration 관련 파라미터
        self.base_epsilon = 0.1          # 기본 탐험 확률
        self.novelty_epsilon = 0.2       # 새로운 시도를 위한 추가 확률
        self.boredom_threshold = 5       # 같은 요리 반복 임계값
        self.seasonal_boost = 0.15       # 제철 재료 추천 확률 증가
        
        # 레시피 데이터
        self.recipes_db = self._initialize_recipe_db()
        self.seasonal_ingredients = self._initialize_seasonal_ingredients()
        self.cuisine_ingredients = self._initialize_cuisine_ingredients()
        
        # 선택 히스토리 및 피드백 저장
        self.choice_history = {}  # 사용자의 선택 기록
        self.feedback_history = {}  # 피드백 기록
        
        # 추천 옵션 가중치
        self.recommendation_weights = {
            'safe': 0.4,      # 안전한 선택 (자주 만들던 요리)
            'moderate': 0.3,  # 약간의 변화
            'explore': 0.2,   # 새로운 시도
            'fusion': 0.1     # 완전히 다른 스타일
        }

    def _initialize_recipe_db(self) -> Dict:
        """레시피 데이터베이스 초기화"""
        return {
            'kimchi_stew': {
                'ingredients': ['kimchi', 'pork', 'tofu', 'green_onion'],
                'difficulty': 2,
                'cuisine': 'korean',
                'time': 30,
                'season': ['winter', 'fall']
            },
            'pasta_carbonara': {
                'ingredients': ['pasta', 'bacon', 'egg', 'garlic'],
                'difficulty': 3,
                'cuisine': 'italian',
                'time': 20,
                'season': ['all']
            },
            'vegetable_curry': {
                'ingredients': ['potato', 'carrot', 'onion', 'curry_powder'],
                'difficulty': 2,
                'cuisine': 'indian',
                'time': 40,
                'season': ['winter']
            },
            'bibimbap': {
                'ingredients': ['rice', 'spinach', 'carrot', 'egg', 'beef'],
                'difficulty': 3,
                'cuisine': 'korean',
                'time': 35,
                'season': ['spring', 'summer']
            },
            'stir_fry': {
                'ingredients': ['chicken', 'bell_pepper', 'onion', 'soy_sauce'],
                'difficulty': 2,
                'cuisine': 'chinese',
                'time': 25,
                'season': ['all']
            }
        }
    
    def _initialize_seasonal_ingredients(self) -> Dict[str, List[str]]:
        """계절별 식재료 초기화"""
        return {
            'spring': ['spinach', 'strawberry', 'asparagus', 'spring_onion'],
            'summer': ['tomato', 'cucumber', 'eggplant', 'watermelon'],
            'fall': ['mushroom', 'sweet_potato', 'pumpkin', 'apple'],
            'winter': ['radish', 'cabbage', 'potato', 'garlic']
        }
    
    def _initialize_cuisine_ingredients(self) -> Dict[str, List[str]]:
        """각 나라별 대표 식재료 초기화"""
        return {
            'korean': ['kimchi', 'gochugaru', 'sesame_oil', 'soybean_paste'],
            'japanese': ['miso', 'wasabi', 'seaweed', 'dashi'],
            'chinese': ['soy_sauce', 'oyster_sauce', 'five_spice', 'hoisin'],
            'italian': ['basil', 'olive_oil', 'parmesan', 'tomato'],
            'indian': ['curry_powder', 'turmeric', 'cumin', 'coriander']
        }

    def generate_recommendations(self, state: Dict) -> Tuple[Dict, Dict]:
        """다양한 수준의 추천 생성"""
        recommendations = {
            'safe': self._get_safe_recommendation(state),
            'moderate': self._get_moderate_recommendation(state),
            'explore': self._get_exploratory_recommendation(state),
            'fusion': self._get_fusion_recommendation(state)
        }
        
        descriptions = {
            'safe': {
                'title': '익숙한 요리',
                'description': '자주 만들어본 익숙한 요리입니다.',
                'confidence': '성공 확률이 매우 높습니다.',
                'ingredients_owned': self._calculate_owned_ingredients(
                    state['current_ingredients'],
                    recommendations['safe']['required_ingredients']
                )
            },
            'moderate': {
                'title': '약간의 변화',
                'description': '익숙한 요리에 새로운 재료나 방법을 더해봅니다.',
                'confidence': '성공 확률이 높은 편입니다.',
                'ingredients_owned': self._calculate_owned_ingredients(
                    state['current_ingredients'],
                    recommendations['moderate']['required_ingredients']
                )
            },
            'explore': {
                'title': '새로운 도전',
                'description': '처음 시도해보는 색다른 요리입니다.',
                'confidence': '도전적이지만 충분히 가능합니다.',
                'ingredients_owned': self._calculate_owned_ingredients(
                    state['current_ingredients'],
                    recommendations['explore']['required_ingredients']
                )
            },
            'fusion': {
                'title': '퓨전 스타일',
                'description': '전혀 다른 스타일을 조합한 새로운 요리입니다.',
                'confidence': '실험적인 도전이 될 수 있습니다.',
                'ingredients_owned': self._calculate_owned_ingredients(
                    state['current_ingredients'],
                    recommendations['fusion']['required_ingredients']
                )
            }
        }
        
        return recommendations, descriptions
    
    def _get_safe_recommendation(self, state: Dict) -> Dict:
        """안전한 선택 추천"""
        successful_recipes = state.get('successful_recipes', [])
        if successful_recipes:
            recipe_name = random.choice(successful_recipes)
            recipe = self.recipes_db[recipe_name]
            return {
                'recipe_name': recipe_name,
                'required_ingredients': recipe['ingredients'],
                'difficulty': recipe['difficulty'],
                'cuisine': recipe['cuisine'],
                'time': recipe['time']
            }
        return self._get_moderate_recommendation(state)
    
    def _get_moderate_recommendation(self, state: Dict) -> Dict:
        """적당한 변화가 있는 추천"""
        successful_recipes = state.get('successful_recipes', [])
        if successful_recipes:
            base_recipe_name = random.choice(successful_recipes)
            base_recipe = self.recipes_db[base_recipe_name]
            
            modified_ingredients = base_recipe['ingredients'].copy()
            seasonal_ingredient = random.choice(self.seasonal_ingredients[state['season']])
            if seasonal_ingredient not in modified_ingredients:
                modified_ingredients.append(seasonal_ingredient)
            
            return {
                'recipe_name': f"{base_recipe_name} (변형)",
                'required_ingredients': modified_ingredients,
                'difficulty': base_recipe['difficulty'] + 0.5,
                'cuisine': base_recipe['cuisine'],
                'time': base_recipe['time'] + 10  # 새로운 재료로 인한 추가 시간
            }
        return self._get_exploratory_recommendation(state)
    
    def _get_exploratory_recommendation(self, state: Dict) -> Dict:
        """새로운 시도 추천"""
        tried_recipes = set(state['cooking_history'])
        available_recipes = [name for name in self.recipes_db.keys() 
                           if name not in tried_recipes]
        
        if available_recipes:
            recipe_name = random.choice(available_recipes)
            recipe = self.recipes_db[recipe_name]
            return {
                'recipe_name': recipe_name,
                'required_ingredients': recipe['ingredients'],
                'difficulty': recipe['difficulty'],
                'cuisine': recipe['cuisine'],
                'time': recipe['time']
            }
        return self._get_fusion_recommendation(state)
    
    def _get_fusion_recommendation(self, state: Dict) -> Dict:
        """퓨전 스타일 추천"""
        cuisines = list(self.cuisine_ingredients.keys())
        cuisine1, cuisine2 = random.sample(cuisines, 2)
        
        ingredients1 = random.sample(self.cuisine_ingredients[cuisine1], 2)
        ingredients2 = random.sample(self.cuisine_ingredients[cuisine2], 2)
        
        # 기본 재료 추가
        base_ingredients = ['onion', 'garlic', 'salt']
        
        return {
            'recipe_name': f"{cuisine1}-{cuisine2} 퓨전",
            'required_ingredients': ingredients1 + ingredients2 + base_ingredients,
            'difficulty': 4,
            'cuisine': 'fusion',
            'time': 45  # 퓨전 요리는 시간 여유 있게
        }
    
    def _calculate_owned_ingredients(self, current_ingredients: List[str], 
                                   required_ingredients: List[str]) -> Dict:
        """현재 보유한 재료 비율 계산"""
        owned = set(current_ingredients) & set(required_ingredients)
        return {
            'owned': list(owned),
            'missing': list(set(required_ingredients) - set(current_ingredients)),
            'percentage': len(owned) / len(required_ingredients) * 100
        }
    
    def update_weights(self, choice: str, success_rating: float) -> None:
        """사용자 선택과 결과에 따라 가중치 업데이트"""
        if success_rating > 4:  # 매우 성공적
            self.recommendation_weights[choice] = min(
                self.recommendation_weights[choice] + 0.05, 
                0.5  # 최대 가중치 제한
            )
        elif success_rating < 2:  # 실패에 가까움
            self.recommendation_weights[choice] = max(
                self.recommendation_weights[choice] - 0.03,
                0.1  # 최소 가중치 제한
            )
        
        # 가중치 정규화
        total = sum(self.recommendation_weights.values())
        for key in self.recommendation_weights:
            self.recommendation_weights[key] /= total
    
    def record_choice(self, state: Dict, choice: str, recommendation: Dict, success_rating: float) -> None:
        """사용자의 선택과 결과 기록"""
        choice_key = (state['season'], choice)
        if choice_key not in self.choice_history:
            self.choice_history[choice_key] = []
            
        self.choice_history[choice_key].append({
            'recipe': recommendation['recipe_name'],
            'rating': success_rating,
            'timestamp': datetime.now().isoformat(),
            'ingredients': recommendation['required_ingredients'],
            'difficulty': recommendation['difficulty']
        })
        
        # 가중치 업데이트
        self.update_weights(choice, success_rating)
        
        # 피드백 히스토리 업데이트
        recipe_key = recommendation['recipe_name']
        if recipe_key not in self.feedback_history:
            self.feedback_history[recipe_key] = []
        
        self.feedback_history[recipe_key].append({
            'rating': success_rating,
            'timestamp': datetime.now().isoformat(),
            'choice_type': choice
        })

        # successful_recipes 업데이트 시 기본 레시피 이름만 저장
        if success_rating >= 4:
            # 변형 레시피의 경우 원본 레시피 이름만 저장
            base_recipe_name = recipe_key.split(' (변형)')[0]
            if base_recipe_name in self.recipes_db:  # 기존 레시피인 경우에만 추가
                state['successful_recipes'].append(base_recipe_name)

def get_current_season() -> str:
    """현재 계절 반환"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    elif month in [9, 10, 11]:
        return 'fall'
    else:
        return 'winter'

def simulate_cooking_history(num_days: int = 30) -> List[str]:
    """테스트용 조리 이력 생성"""
    recipes = ['kimchi_stew', 'pasta_carbonara', 'vegetable_curry', 
              'bibimbap', 'stir_fry']
    return [random.choice(recipes) for _ in range(num_days)]

def simulate_successful_recipes() -> List[str]:
    """테스트용 성공한 레시피 목록 생성"""
    return ['kimchi_stew', 'vegetable_curry', 'stir_fry']

def print_recommendation(category: str, recommendation: Dict, 
                        description: Dict) -> None:
    """추천 정보 출력"""
    print(f"\n[{description['title']}]")
    print(f"추천 요리: {recommendation['recipe_name']}")
    print(f"필요한 재료: {', '.join(recommendation['required_ingredients'])}")
    print(f"설명: {description['description']}")
    print(f"난이도: {recommendation['difficulty']}/5")
    print(f"예상 소요시간: {recommendation['time']}분")
    print(f"보유 재료 비율: {description['ingredients_owned']['percentage']:.1f}%")
    print(f"추가로 필요한 재료: {', '.join(description['ingredients_owned']['missing'])}")
    print(f"자신감 수준: {description['confidence']}")

def main():
    """메인 실행 함수"""
    recommender = RecipeRecommender()
    
    # 테스트 상태 설정
    test_state = {
        'current_ingredients': ['onion', 'potato', 'carrot', 'garlic', 'egg'],
        'cooking_history': simulate_cooking_history(),
        'successful_recipes': simulate_successful_recipes(),
        'user_preferences': {'spicy': 0.8, 'vegetarian': 0.3},
        'season': get_current_season()
    }
    
    print("=== 요리 추천 시스템 테스트 ===")
    print(f"\n현재 계절: {test_state['season']}")
    print(f"보유 재료: {', '.join(test_state['current_ingredients'])}")
    print(f"\n최근 요리 기록: {', '.join(test_state['cooking_history'][-5:])}")
    print(f"성공한 요리: {', '.join(test_state['successful_recipes'])}")
    
    # 추천 받기
    recommendations, descriptions = recommender.generate_recommendations(test_state)
    
    # 각 추천 옵션 출력
    for category in ['safe', 'moderate', 'explore', 'fusion']:
        print_recommendation(category, recommendations[category], descriptions[category])
    
    # 30일간의 시뮬레이션
    print("\n=== 30일 추천 시뮬레이션 ===")
    
    simulation_results = {
        'safe': {'count': 0, 'total_rating': 0},
        'moderate': {'count': 0, 'total_rating': 0},
        'explore': {'count': 0, 'total_rating': 0},
        'fusion': {'count': 0, 'total_rating': 0}
    }
    
    for day in range(30):
        print(f"\n[Day {day + 1}]")
        recommendations, descriptions = recommender.generate_recommendations(test_state)
        
        # 선택 시뮬레이션 (가중치 기반)
        choice = random.choices(
            list(recommender.recommendation_weights.keys()),
            list(recommender.recommendation_weights.values())
        )[0]
        
        # 성공 확률은 선택한 카테고리에 따라 다르게 설정
        base_success_rates = {
            'safe': 0.9,
            'moderate': 0.7,
            'explore': 0.5,
            'fusion': 0.3
        }
        
        # 보유 재료 비율에 따른 보너스
        ingredients_ratio = descriptions[choice]['ingredients_owned']['percentage'] / 100
        success_bonus = ingredients_ratio * 0.2
        
        # 최종 성공 확률 계산
        success_rate = min(base_success_rates[choice] + success_bonus, 1.0)
        
        # 평가 점수 생성 (1-5)
        base_rating = 5 if random.random() < success_rate else random.uniform(1, 3)
        variation = random.uniform(-0.5, 0.5)
        success_rating = max(1, min(5, base_rating + variation))
        
        # 결과 기록
        simulation_results[choice]['count'] += 1
        simulation_results[choice]['total_rating'] += success_rating
        
        # 선택 결과 기록
        recommender.record_choice(test_state, choice, recommendations[choice], success_rating)
        
        # 상태 업데이트
        base_recipe_name = recommendations[choice]['recipe_name'].split(' (변형)')[0]
        test_state['cooking_history'].append(base_recipe_name)
        
        # 성공한 경우에만 successful_recipes에 추가
        if success_rating >= 4:
            # 변형 레시피의 경우 원본 레시피 이름만 저장
            if base_recipe_name in recommender.recipes_db:
                test_state['successful_recipes'].append(base_recipe_name)
        
        # 보유 재료 업데이트 (시뮬레이션을 위한 간단한 로직)
        test_state['current_ingredients'] = list(set(
            test_state['current_ingredients'] + 
            random.sample(recommendations[choice]['required_ingredients'], 
                         k=min(3, len(recommendations[choice]['required_ingredients'])))
        ))[:7]  # 최대 7개 재료만 유지
        
        print(f"선택한 요리: {recommendations[choice]['recipe_name']} ({choice})")
        print(f"평가 점수: {success_rating:.1f}/5.0")
        print(f"현재 보유 재료: {', '.join(test_state['current_ingredients'])}")
    
    # 시뮬레이션 결과 출력
    print("\n=== 시뮬레이션 결과 ===")
    for category in simulation_results:
        count = simulation_results[category]['count']
        if count > 0:
            avg_rating = simulation_results[category]['total_rating'] / count
            print(f"\n{descriptions[category]['title']}")
            print(f"선택 횟수: {count}회")
            print(f"평균 평가: {avg_rating:.2f}/5.0")
            print(f"최종 가중치: {recommender.recommendation_weights[category]:.3f}")

if __name__ == "__main__":
    main()