from typing import List
from sqlalchemy.orm import Session
from crud.base import CRUDBase
from models.models import Recipe
from schemas.recipes import RecipeCreate, Recipe as RecipeSchema

class CRUDRecipe(CRUDBase[Recipe, RecipeCreate, RecipeSchema]):
    pass

recipe = CRUDRecipe(Recipe)