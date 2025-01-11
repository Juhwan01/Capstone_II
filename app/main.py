from fastapi import FastAPI
from api.routes.ingredients import router as ingredients_router
from db.init_db import init_db

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(ingredients_router, prefix="/ingredients", tags=["Ingredients"])
