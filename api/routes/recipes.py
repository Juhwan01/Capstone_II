from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import random

from api.dependencies import get_db, get_current_user
from schemas.recipes import Recipe, RecipeCreate, RecommendationResponse
from schemas.user import UserProfile
from services.recommender import RecipeRecommender
from crud.crud_recipe import recipe
from crud.crud_user import user
from models.models import QValue, User

router = APIRouter(prefix="/recipes", tags=["recipes"])
recommender = RecipeRecommender()

@router.post("/", response_model=Recipe)
def create_recipe(
    recipe_in: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipe_in_dict = recipe_in.dict()
    recipe_in_dict["created_by"] = current_user.id
    return recipe.create(db=db, obj_in=recipe_in_dict)

@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    db_recipe = recipe.get(db=db, id=recipe_id)
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe

@router.get("/recommendations/", response_model=List[RecommendationResponse])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    recipes = recipe.get_multi(db=db)
    user_profile = UserProfile.from_orm(current_user.profile)
    
    q_values = {
        qv.recipe_id: qv.value 
        for qv in db.query(QValue).filter(QValue.user_id == current_user.id).all()
    }
    
    recipe_scores = [
        (rec, recommender.calculate_recipe_score(
            Recipe.from_orm(rec),
            user_profile,
            q_values.get(rec.id, 0)
        ))
        for rec in recipes
    ]
    
    recipe_scores.sort(key=lambda x: x[1], reverse=True)
    recommendations = recipe_scores[:3]
    
    remaining_recipes = [r for r, _ in recipe_scores[3:]]
    if remaining_recipes:
        exploration_recipe = random.choice(remaining_recipes)
        recommendations.append((exploration_recipe, 0))
    
    return [
        RecommendationResponse(
            recipe=Recipe.from_orm(recipe),
            score=score,
            is_exploration=(i == 3)
        )
        for i, (recipe, score) in enumerate(recommendations)
    ]