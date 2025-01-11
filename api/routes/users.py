from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from api.dependencies import get_db, get_current_user
from schemas.user import UserProfile, UserProfileCreate
from crud.crud_user import user
from models.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me/profile", response_model=UserProfile)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return current_user.profile

@router.put("/me/ingredients", response_model=UserProfile)
def update_ingredients(
    ingredients: Dict[str, float],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    db_profile = user.update_ingredients(
        db=db,
        user_id=current_user.id,
        ingredients=ingredients
    )
    return db_profile