from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Ingredient
import math
import asyncio
from typing import List, Dict, Tuple

class IngredientMatcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ingredient_categories = {
            '채소류': 0.8,
            '과일류': 0.8,
            '육류': 0.9,
            '해산물': 0.9,
            '유제품': 0.7,
            '가공식품': 0.5
        }

    def calculate_freshness_score(self, expiry_date: datetime) -> float:
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
        lat1, lon1 = location1
        lat2, lon2 = location2
        R = 6371  # 지구 반경 (km)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        return max(0, 1 - (distance / 5))  # 5km 이상이면 0점

    def calculate_value_score(self, item1_value: float, item2_value: float) -> float:
        if item1_value == 0 or item2_value == 0:
            return 0.0
        ratio = min(item1_value, item2_value) / max(item1_value, item2_value)
        return ratio

    def calculate_user_preference_score(self, user_preferences: dict, item_category: str) -> float:
        return user_preferences.get(item_category, 0.5)

    def calculate_name_similarity_score(self, name1: str, name2: str) -> float:
        return 1.0 if name1 == name2 else 0.0

    async def fetch_requested_item(self, name: str) -> dict:
        result = await self.db.execute(select(Ingredient).where(Ingredient.name == name))
        requested_item = result.scalars().first()
        if not requested_item:
            raise ValueError(f"No ingredient found with name '{name}'")
        return {
            "name": requested_item.name,
            "category": requested_item.category,
            "expiry_date": requested_item.expiry_date,
            "value": requested_item.value,
            "location": (37.5665, 126.9780),  # 예시: 요청자 위치
        }

    
    async def find_matches_for_request(self, name: str) -> dict:
        try:
            # 요청된 식재료 데이터 가져오기
            requested_item = await self.fetch_requested_item(name)

            # 제공 가능한 식재료 데이터베이스에서 조회
            result = await self.db.execute(select(Ingredient))
            available_items = result.scalars().all()

            # 제공 가능한 식재료를 딕셔너리로 변환
            available_items_dict = [
                {
                    "name": item.name,
                    "category": item.category,
                    "expiry_date": item.expiry_date,
                    "value": item.value,
                    "location": (item.location_lat, item.location_lon),  # 위치가 DB에 저장되어 있다고 가정
                }
                for item in available_items
            ]

            # 사용자 선호도 및 위치 (예시 데이터)
            user_preferences = {"채소류": 0.9}
            user_location = (37.5665, 126.9780)

            # 매칭 로직 실행
            exact_matches = []
            similar_matches = []

            for available in available_items_dict:
                freshness = self.calculate_freshness_score(available["expiry_date"])
                distance = self.calculate_distance_score(user_location, available["location"])
                value_balance = self.calculate_value_score(available["value"], requested_item["value"])
                preference = self.calculate_user_preference_score(user_preferences, available["category"])
                name_similarity = self.calculate_name_similarity_score(available["name"], requested_item["name"])
                category_weight = self.ingredient_categories.get(available["category"], 0.5)

                total_score = (
                    freshness * 0.3 +
                    distance * 0.25 +
                    value_balance * 0.2 +
                    preference * 0.15 +
                    name_similarity * 0.15
                ) * category_weight

                match_info = {
                    "매칭 점수": round(total_score, 2),
                    "제공 식재료": f"{available['name']} (가치: {available['value']}원)",
                    "상세 점수": {
                    "신선도": round(freshness, 2),
                    "거리": round(distance, 2),
                    "가치 균형": round(value_balance, 2),
                    "선호도": round(preference, 2),
                    "이름 유사도": round(name_similarity, 2),
                }
                }

                if name_similarity == 1.0:
                    exact_matches.append(match_info)
                elif available["category"] == requested_item["category"]:
                    similar_matches.append(match_info)

            exact_matches.sort(key=lambda x: x["매칭 점수"], reverse=True)
            similar_matches.sort(key=lambda x: x["매칭 점수"], reverse=True)

            return {
                "정확히 일치하는 매칭": exact_matches,
                "비슷한 식재료 추천": similar_matches
            }
        except ValueError as e:
            return {"error": str(e)}

