from fastapi import FastAPI
from api.routes.ingredients import router as ingredients_router
from api.routes.transaction import router as transaction_router

from db.init_db import init_db
import uvicorn

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(ingredients_router, prefix="/ingredients", tags=["Ingredients"])
app.include_router(transaction_router, prefix="/transaction", tags=["Transaction"])
# uvicorn 실행 코드
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)