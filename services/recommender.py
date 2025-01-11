from typing import List, Tuple
import random
from schemas.recipes import Recipe
from schemas.user import UserProfile

class RecipeRecommender:
    def calculate_ingredient_match_score(self, recipe: Recipe, user_profile: UserProfile) -> float:
        available_ingredients = set(user_profile.owned_ingredients.keys())
        required_ingredients = set(recipe.ingredients.keys())
        
        matching_count = len(available_ingredients.intersection(required_ingredients))
        total_count = len(required_ingredients)
        
        return matching_count / total_count if total_count > 0 else 0

    def can_cook(self, recipe: Recipe, user_profile: UserProfile) -> bool:
        return all(user_profile.owned_ingredients.get(ing, 0) >= amt 
                  for ing, amt in recipe.ingredients.items())

    def calculate_recipe_score(self, recipe: Recipe, user_profile: UserProfile, q_value: float) -> float:
        if not self.can_cook(recipe, user_profile):
            return 0.1
            
        ingredient_score = self.calculate_ingredient_match_score(recipe, user_profile)
        difficulty_match = 1 - abs(recipe.difficulty - user_profile.cooking_skill) / 4
        time_match = 1 - abs(recipe.cooking_time - user_profile.preferred_cooking_time) / 60
        
        return (ingredient_score * 0.4 +
                difficulty_match * 0.2 +
                time_match * 0.1 +
                q_value * 0.3)