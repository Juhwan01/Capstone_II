import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple

class IngredientMatcher:
    def __init__(self):
        self.ingredient_categories = {
            '채소류': 0.8,
            '과일류': 0.8,
            '육류': 0.9,
            '해산물': 0.9,
            '유제품': 0.7,
            '가공식품': 0.5
        }
    
    def calculate_freshness_score(self, expiry_date: datetime) -> float:
        """유통기한 기반 신선도 점수 계산
        - 유통기한 지남: 0점
        - 3일 이내: 0.3점
        - 7일 이내: 0.5점
        - 14일 이내: 0.7점
        - 21일 이내: 0.8점
        - 30일 이내: 0.9점
        - 30일 이상: 1.0점
        """
        days_until_expiry = (expiry_date - datetime.now()).days
        
        if days_until_expiry <= 0:
            return 0.0
        elif days_until_expiry <= 3:
            return 0.3
        elif days_until_expiry <= 7:
            return 0.5
        elif days_until_expiry <= 14:
            return 0.7
        elif days_until_expiry <= 21:
            return 0.8
        elif days_until_expiry <= 30:
            return 0.9
        else:
            return 1.0

    def calculate_distance_score(self, location1: tuple, location2: tuple) -> float:
        """위치 기반 거리 점수 계산"""
        import math
        
        lat1, lon1 = location1
        lat2, lon2 = location2
        
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return max(0, 1 - (distance / 5))  # 5km 이상이면 0점

    def calculate_value_score(self, item1_value: float, item2_value: float) -> float:
        """교환 가치의 균형 점수 계산"""
        if item1_value == 0 or item2_value == 0:
            return 0.0
        ratio = min(item1_value, item2_value) / max(item1_value, item2_value)
        return ratio

    def calculate_user_preference_score(self, user_preferences: dict, item_category: str) -> float:
        """사용자 선호도 기반 점수 계산"""
        return user_preferences.get(item_category, 0.5)
    
    def calculate_name_similarity_score(self, name1: str, name2: str) -> float:
        """식재료 이름 유사도 점수 계산"""
        return 1.0 if name1 == name2 else 0.0

    def find_matches_for_request(self, requested_item: dict, available_items: list, 
                               user_location: tuple, user_preferences: dict) -> list:
        """특정 요청 식재료에 대한 매칭 찾기"""
        matches = []
        
        # 1단계: 정확히 같은 이름의 식재료 찾기
        exact_matches = []
        similar_matches = []
        
        for available in available_items:
            # 기본 점수 계산
            freshness = self.calculate_freshness_score(available['expiry_date'])
            distance = self.calculate_distance_score(user_location, available['location'])
            value_balance = self.calculate_value_score(available['value'], requested_item['value'])
            preference = self.calculate_user_preference_score(user_preferences, available['category'])
            
            # 이름 유사도 점수
            name_similarity = self.calculate_name_similarity_score(
                available['name'], requested_item['name']
            )
            
            # 카테고리 가중치
            category_weight = self.ingredient_categories.get(available['category'], 0.5)
            
            # 종합 점수 계산
            total_score = (
                freshness * 0.25 +
                distance * 0.25 +
                value_balance * 0.2 +
                preference * 0.15 +
                name_similarity * 0.15
            ) * category_weight
            
            match_info = {
                'available_item': available,
                'requested_item': requested_item,
                'score': total_score,
                'match_details': {
                    'freshness_score': freshness,
                    'distance_score': distance,
                    'value_score': value_balance,
                    'preference_score': preference,
                    'name_similarity': name_similarity
                }
            }
            
            # 정확히 같은 이름이면 exact_matches에, 아니면 similar_matches에 추가
            if name_similarity == 1.0:
                exact_matches.append(match_info)
            elif available['category'] == requested_item['category']:
                similar_matches.append(match_info)
        
        # 점수순으로 정렬
        exact_matches.sort(key=lambda x: x['score'], reverse=True)
        similar_matches.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'exact_matches': exact_matches,
            'similar_matches': similar_matches
        }

    def find_optimal_matches(self, requested_items: list, available_items: list, 
                           user_location: tuple, user_preferences: dict) -> dict:
        """모든 요청 식재료에 대한 매칭 찾기"""
        all_matches = {}
        
        for requested_item in requested_items:
            matches = self.find_matches_for_request(
                requested_item, available_items, user_location, user_preferences
            )
            all_matches[requested_item['name']] = matches
            
        return all_matches


# 테스트 실행
if __name__ == "__main__":
    matcher = IngredientMatcher()
    
    # 테스트 데이터 - 제공 가능한 식재료
    available_items = [
        {
            'id': '1',
            'name': '양파',  # 동일한 식재료 추가
            'category': '채소류',
            'expiry_date': datetime(2025, 1, 30),
            'value': 2500,
            'location': (37.5665, 126.9780),  # 서울시청
            'nutrition': {'칼로리': 40, '단백질': 1.1, '탄수화물': 9}
        },
        {
            'id': '2',
            'name': '양파',  # 다른 위치의 양파
            'category': '채소류',
            'expiry_date': datetime(2025, 1, 28),
            'value': 2000,
            'location': (37.5642, 126.9744),  # 서울시청 근처
            'nutrition': {'칼로리': 40, '단백질': 1.1, '탄수화물': 9}
        },
        {
            'id': '3',
            'name': '당근',  # 같은 카테고리 다른 채소
            'category': '채소류',
            'expiry_date': datetime(2025, 1, 25),
            'value': 3000,
            'location': (37.5511, 126.9882),  # 용산
            'nutrition': {'칼로리': 41, '단백질': 0.9, '탄수화물': 10}
        },
        {
            'id': '4',
            'name': '감자',  # 같은 카테고리 다른 채소
            'category': '채소류',
            'expiry_date': datetime(2025, 1, 22),
            'value': 4500,
            'location': (37.5757, 126.9768),  # 종로
            'nutrition': {'칼로리': 77, '단백질': 2.0, '탄수화물': 17}
        }
    ]
    
    # 테스트 데이터 - 요청된 식재료
    requested_items = [
        {
            'id': '5',
            'name': '양파',
            'category': '채소류',
            'expiry_date': datetime(2025, 1, 28),
            'value': 2000,
            'location': (37.5665, 126.9780),
            'nutrition': {'칼로리': 40, '단백질': 1.1, '탄수화물': 9}
        }
    ]
    
    # 테스트 위치 (서울시청)
    test_location = (37.5665, 126.9780)
    
    # 테스트 사용자 선호도
    test_preferences = {
        '채소류': 0.8,
        '과일류': 0.7,
        '육류': 0.9,
        '해산물': 0.6,
        '유제품': 0.5
    }
    
    # 매칭 실행
    matches = matcher.find_optimal_matches(requested_items, available_items, test_location, test_preferences)
    
    # 결과 출력
    for requested_name, match_results in matches.items():
        print(f"\n=== '{requested_name}' 매칭 결과 ===")
        
        # 정확히 일치하는 매칭 결과
        print("\n🎯 정확히 일치하는 매칭:")
        if match_results['exact_matches']:
            for i, match in enumerate(match_results['exact_matches'], 1):
                print(f"\n매칭 #{i}")
                print(f"매칭 점수: {match['score']:.2f}")
                print(f"제공 식재료: {match['available_item']['name']} (가치: {match['available_item']['value']}원)")
                print("상세 점수:")
                print(f"- 신선도: {match['match_details']['freshness_score']:.2f}")
                print(f"- 거리: {match['match_details']['distance_score']:.2f}")
                print(f"- 가치 균형: {match['match_details']['value_score']:.2f}")
                print(f"- 선호도: {match['match_details']['preference_score']:.2f}")
        else:
            print("정확히 일치하는 매칭이 없습니다.")
            
        # 유사한 매칭 결과
        print("\n🔍 비슷한 식재료 추천:")
        if match_results['similar_matches']:
            for i, match in enumerate(match_results['similar_matches'], 1):
                print(f"\n추천 #{i}")
                print(f"매칭 점수: {match['score']:.2f}")
                print(f"추천 식재료: {match['available_item']['name']} (가치: {match['available_item']['value']}원)")
                print("상세 점수:")
                print(f"- 신선도: {match['match_details']['freshness_score']:.2f}")
                print(f"- 거리: {match['match_details']['distance_score']:.2f}")
                print(f"- 가치 균형: {match['match_details']['value_score']:.2f}")
                print(f"- 선호도: {match['match_details']['preference_score']:.2f}")
        else:
            print("비슷한 식재료 추천이 없습니다.")