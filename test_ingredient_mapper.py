import unittest
from utils.ingredient_mapper import IngredientMapper

class TestIngredientMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = IngredientMapper(threshold=0.5)
    
    def test_preprocess_ingredient(self):
        test_cases = [
            ("양파(중간크기)", "양파"),
            ("양파 1개", "양파"),
            ("CJ 햇반", "햇반"),
            ("국산 감자 2kg", "감자"),
            ("펩시콜라 1.5L", "콜라"),
            ("코카콜라 제로 355ml", "콜라"),
            ("불닭볶음면 5봉지", "불닭볶음면"),
            ("청정원 멸치액젓 200ml", "멸치액젓"),
        ]
        
        for input_str, expected in test_cases:
            result = self.mapper._preprocess_ingredient(input_str)
            self.assertEqual(result, expected)
    
    def test_map_ingredient(self):
        test_cases = [
            # 정확히 일치하는 경우
            ("양파", "양파"),
            ("소금", "소금"),
            # 유사한 경우
            ("양파(중간크기)", "양파"),
            ("청정원 멸치액젓", "멸치액젓"),
            ("펩시콜라", "콜라"),
            ("코카콜라 제로", "콜라"),
            # 매핑되지 않는 경우
            ("XYZ 특수조미료", None),
        ]
        
        for input_str, expected in test_cases:
            result = self.mapper.map_ingredient(input_str)
            self.assertEqual(result, expected)
    
    def test_map_ingredients(self):
        ingredients = {
            "양파 2개": 2,
            "청정원 소금 약간": 0.5,
            "펩시콜라 1.5L": 1.5,
            "XYZ 특수조미료": 1
        }
        
        expected = {
            "양파": 2,
            "소금": 0.5,
            "콜라": 1.5
        }
        
        result = self.mapper.map_ingredients(ingredients)
        self.assertEqual(result, expected)
    
    def test_can_cook(self):
        recipe_ingredients = {
            "양파": 2,
            "소금": 0.5,
            "콜라": 1
        }
        
        # 요리 가능한 경우
        owned_ingredients = {
            "양파 3개": 3,
            "청정원 소금": 1,
            "펩시콜라": 2
        }
        self.assertTrue(self.mapper.can_cook(recipe_ingredients, owned_ingredients))
        
        # 부족한 경우
        owned_ingredients = {
            "양파 1개": 1,
            "청정원 소금": 1,
            "펩시콜라": 2
        }
        self.assertFalse(self.mapper.can_cook(recipe_ingredients, owned_ingredients))
    
    def test_calculate_ingredient_match_score(self):
        recipe_ingredients = {
            "양파": 2,
            "소금": 0.5,
            "콜라": 1,
            "후추": 0.1
        }
        
        # 완벽한 매칭
        owned_ingredients = {
            "양파 3개": 3,
            "청정원 소금": 1,
            "펩시콜라": 2,
            "후추": 0.2
        }
        score = self.mapper.calculate_ingredient_match_score(recipe_ingredients, owned_ingredients)
        self.assertAlmostEqual(score, 1.0, places=1)
        
        # 부분 매칭 (75% 재료, 충분한 수량)
        owned_ingredients = {
            "양파 3개": 3,
            "청정원 소금": 1,
            "펩시콜라": 2
        }
        score = self.mapper.calculate_ingredient_match_score(recipe_ingredients, owned_ingredients)
        self.assertAlmostEqual(score, 0.75, places=1)
        
        # 부분 매칭 (75% 재료, 부족한 수량)
        owned_ingredients = {
            "양파 1개": 1,  # 부족
            "청정원 소금": 1,
            "펩시콜라": 2
        }
        score = self.mapper.calculate_ingredient_match_score(recipe_ingredients, owned_ingredients)
        self.assertLess(score, 0.75)

if __name__ == "__main__":
    unittest.main()