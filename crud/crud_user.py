from typing import Dict, List, Optional, Union, Any
from sqlalchemy.orm import Session
from crud.base import CRUDBase
from models.models import UserProfile
from schemas.user import UserProfileCreate, UserProfileUpdate

class CRUDUser(CRUDBase[UserProfile, UserProfileCreate, UserProfileUpdate]):
    def create(self, db: Session, *, obj_in: UserProfileCreate, user_id: int) -> UserProfile:
        db_obj = UserProfile(
            user_id=user_id,
            **obj_in.dict()
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_ingredients(
        self, db: Session, *, user_id: int, ingredients: Dict[str, float]
    ) -> Optional[UserProfile]:
        db_obj = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not db_obj:
            return None
            
        current_ingredients = db_obj.owned_ingredients or {}
        for ingredient, amount in ingredients.items():
            current_ingredients[ingredient] = current_ingredients.get(ingredient, 0) + amount
        
        db_obj.owned_ingredients = current_ingredients
        db.commit()
        db.refresh(db_obj)
        return db_obj

user = CRUDUser(UserProfile)