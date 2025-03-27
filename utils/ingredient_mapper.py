from difflib import SequenceMatcher
import re
from typing import Dict, List, Tuple, Optional, Set
import json
import os
from functools import lru_cache

class IngredientMapper:
    def __init__(self, standard_ingredients_file: str = None, threshold: float = 0.6):
        """
        재료 매핑 클래스 초기화
        
        Args:
            standard_ingredients_file: 표준 재료 목록 파일 경로
            threshold: 유사도 임계값 (0~1 사이, 값이 클수록 더 엄격한 매칭)
        """
        self.threshold = threshold
        self.standard_ingredients = self._load_standard_ingredients(standard_ingredients_file)
        self._cache = {}  # 매핑 결과 캐싱
        
    def _load_standard_ingredients(self, file_path: str = None) -> List[str]:
        """표준 재료 목록 로드"""
        # 파일이 없으면 기본 표준 재료 목록 사용
        if not file_path or not os.path.exists(file_path):
            return [
                "쌀", "밀가루", "소금", "설탕", "간장", "고추장", "된장", "콩", "두부", 
                "돼지고기", "소고기", "닭고기", "계란", "우유", "치즈", "버터", "마늘", 
                "양파", "대파", "파", "당근", "감자", "고구마", "배추", "양배추", "상추", 
                "시금치", "콩나물", "무", "오이", "고추", "토마토", "아보카도", "사과", 
                "배", "바나나", "오렌지", "딸기", "포도", "귤", "참기름", "들기름", 
                "올리브유", "식용유", "새우", "꽃게", "홍합", "조개", "오징어", "문어", 
                "고등어", "삼치", "멸치", "김", "미역", "다시마", "밀", "보리", "호밀", 
                "참깨", "들깨", "땅콩", "아몬드", "호두", "잣", "꿀", "물엿", "올리고당", 
                "식초", "레몬즙", "요구르트", "두유", "후추", "고춧가루", "카레가루", 
                "밀가루", "빵가루", "녹차", "홍차", "커피", "콜라", "사이다", "맥주", 
                "소주", "와인", "막걸리", "주스", "소시지", "햄", "베이컨"
            ]
        
        # 파일에서 표준 재료 목록 로드
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"표준 재료 목록 로드 실패: {e}")
            return []
    
    def save_standard_ingredients(self, file_path: str):
        """표준 재료 목록 저장"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.standard_ingredients, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"표준 재료 목록 저장 실패: {e}")
            return False
    
    def add_standard_ingredient(self, ingredient: str):
        """표준 재료 목록에 새 재료 추가"""
        if ingredient and ingredient not in self.standard_ingredients:
            self.standard_ingredients.append(ingredient)
            self._cache = {}  # 캐시 초기화
            return True
        return False
    
    def _preprocess_ingredient(self, ingredient: str) -> str:
        """재료명 전처리"""
        # 소문자 변환 및 공백 제거
        ingredient = ingredient.lower().strip()
        
        # 괄호 안 내용 제거 (예: "양파(중간크기)" -> "양파")
        ingredient = re.sub(r'\([^)]*\)', '', ingredient)
        
        # 수량과 단위 제거 (예: "양파 1개" -> "양파")
        ingredient = re.sub(r'\d+(\.\d+)?(개|g|kg|ml|l|인분|조각|팩|캔|병|줌|컵|스푼|티스푼|큰술|작은술|봉지|통|마리|장|단|뿌리|묶음)', '', ingredient)
        
        # 브랜드명, 원산지 등 추가 정보 제거 (예: "CJ 햇반" -> "햇반")
        common_brands = ["CJ", "대상", "오뚜기", "해태", "농심", "동원", "풀무원", "샘표", "청정원", "롯데", "빙그레", "매일", "서울우유"]
        for brand in common_brands:
            ingredient = ingredient.replace(brand, '').strip()
        
        return ingredient.strip()
    
    @lru_cache(maxsize=1000)
    def _calculate_similarity(self, a: str, b: str) -> float:
        """두 재료명 사이의 유사도 계산"""
        return SequenceMatcher(None, a, b).ratio()
    
    def map_ingredient(self, ingredient: str) -> Optional[str]:
        """
        단일 재료명을 표준 재료명으로 매핑
        
        Args:
            ingredient: 매핑할 재료명
            
        Returns:
            매핑된 표준 재료명 또는 None (매핑 실패시)
        """
        # 캐시 확인
        if ingredient in self._cache:
            return self._cache[ingredient]
        
        # 재료명 전처리
        processed_ingredient = self._preprocess_ingredient(ingredient)
        
        # 정확히 일치하는 표준 재료가 있는지 확인
        if processed_ingredient in self.standard_ingredients:
            self._cache[ingredient] = processed_ingredient
            return processed_ingredient
        
        # 유사도 기반 매핑
        best_match = None
        highest_similarity = 0
        
        for std_ingredient in self.standard_ingredients:
            similarity = self._calculate_similarity(processed_ingredient, std_ingredient)
            if similarity > highest_similarity and similarity >= self.threshold:
                highest_similarity = similarity
                best_match = std_ingredient
        
        # 캐시에 결과 저장
        self._cache[ingredient] = best_match
        return best_match
    
    def map_ingredients(self, ingredients: Dict[str, float]) -> Dict[str, float]:
        """
        여러 재료명과 수량을 표준 재료명으로 매핑
        
        Args:
            ingredients: {재료명: 수량} 형태의 딕셔너리
            
        Returns:
            {표준 재료명: 통합된 수량} 형태의 딕셔너리
        """
        result = {}
        
        for ingredient, amount in ingredients.items():
            mapped = self.map_ingredient(ingredient)
            if mapped:
                # 이미 매핑된 표준 재료가 있으면 수량 합산
                if mapped in result:
                    result[mapped] += amount
                else:
                    result[mapped] = amount
        
        return result
    
    def match_recipe_with_owned(
        self, 
        recipe_ingredients: Dict[str, float], 
        owned_ingredients: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, Dict]]:
        """
        레시피 재료와 보유 재료의 정확한 매칭 및 차감 가능성 판단

        Args:
            recipe_ingredients: 레시피에 필요한 재료와 수량
            owned_ingredients: 사용자가 보유한 재료와 수량

        Returns:
            Tuple containing:
            1. 매칭된 재료와 사용 가능한 수량
            2. 부족하거나 매칭되지 않은 재료 정보
        """
        matched_ingredients = {}
        missing_ingredients = {}

        for recipe_ingredient, required_amount in recipe_ingredients.items():
            best_match = None
            best_match_score = 0
            best_match_owned_amount = 0

            for owned_ingredient, owned_amount in owned_ingredients.items():
                # 유사도 계산 (이름 기반)
                similarity = self._calculate_similarity(recipe_ingredient, owned_ingredient)
                
                # 유사도와 수량 모두 고려한 점수 계산
                match_score = (
                    similarity * 0.7 +  # 이름 유사도 70%
                    min(1, owned_amount / required_amount) * 0.3  # 수량 매칭 30%
                )

                if match_score > best_match_score and match_score >= self.threshold:
                    best_match = owned_ingredient
                    best_match_score = match_score
                    best_match_owned_amount = owned_amount

            if best_match:
                # 사용 가능한 수량 결정
                usable_amount = min(best_match_owned_amount, required_amount)
                
                matched_ingredients[best_match] = usable_amount
                
                # 부족한 재료 추적
                if usable_amount < required_amount:
                    missing_ingredients[best_match] = {
                        "required": required_amount,
                        "owned": best_match_owned_amount,
                        "missing": required_amount - usable_amount
                    }
            else:
                # 완전히 매칭되지 않은 재료
                missing_ingredients[recipe_ingredient] = {
                    "required": required_amount,
                    "owned": 0,
                    "missing": required_amount
                }

        return matched_ingredients, missing_ingredients

    def can_cook(
        self, 
        recipe_ingredients: Dict[str, float], 
        owned_ingredients: Dict[str, float]
    ) -> bool:
        """
        레시피를 만들 수 있는지 정확히 판단

        Args:
            recipe_ingredients: 레시피에 필요한 재료와 수량
            owned_ingredients: 사용자가 보유한 재료와 수량

        Returns:
            레시피 조리 가능 여부 (모든 재료가 충분한 경우 True)
        """
        matched, missing = self.match_recipe_with_owned(
            recipe_ingredients, 
            owned_ingredients
        )
        
        # 부족한 재료가 없으면 요리 가능
        return len(missing) == 0
    
    def get_matched_ingredients(
        self, 
        recipe_ingredients: Dict[str, float], 
        owned_ingredients: Dict[str, float]
    ) -> Set[str]:
        """
        레시피와 보유 재료 중 매칭되는 재료 목록
        
        Args:
            recipe_ingredients: 레시피 필요 재료
            owned_ingredients: 보유 재료
            
        Returns:
            매칭된 재료 집합
        """
        mapped_recipe = self.map_ingredients(recipe_ingredients)
        mapped_owned = self.map_ingredients(owned_ingredients)
        
        return set(mapped_recipe.keys()).intersection(set(mapped_owned.keys()))
    
    def calculate_ingredient_match_score(
        self, 
        recipe_ingredients: Dict[str, float], 
        owned_ingredients: Dict[str, float]
    ) -> float:
        """
        재료 매칭 점수 계산
        
        Args:
            recipe_ingredients: 레시피 필요 재료
            owned_ingredients: 보유 재료
            
        Returns:
            매칭 점수 (0~1)
        """
        # 매핑된 재료 가져오기
        mapped_recipe = self.map_ingredients(recipe_ingredients)
        mapped_owned = self.map_ingredients(owned_ingredients)
        
        # 매칭율 계산 (재료 종류 기준)
        matching_ingredients = set(mapped_recipe.keys()).intersection(set(mapped_owned.keys()))
        total_ingredients = len(mapped_recipe)
        
        if total_ingredients == 0:
            return 0
            
        # 재료 매칭 점수
        type_match_score = len(matching_ingredients) / total_ingredients
        
        # 수량 매칭 계산
        quantity_scores = []
        for ingredient in matching_ingredients:
            required = mapped_recipe[ingredient]
            owned = mapped_owned[ingredient]
            
            if required <= 0:
                continue
                
            # 필요량 대비 보유량 비율 (최대 1.0)
            ratio = min(owned / required, 1.0)
            quantity_scores.append(ratio)
        
        # 수량 매칭 점수
        quantity_match_score = sum(quantity_scores) / len(quantity_scores) if quantity_scores else 0
        
        # 최종 점수 (재료 종류 60%, 수량 40%)
        return (type_match_score * 0.6) + (quantity_match_score * 0.4)