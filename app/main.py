from fastapi import FastAPI
from api.routes.ingredients import router as ingredients_router
from api.routes.chat import router as chat_router
from db.init_db import init_db
from core.config import CORSMiddleware
import uvicorn

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()


# CORS 설정 추가
CORSMiddleware(app)

app.include_router(ingredients_router, prefix="/ingredients", tags=["Ingredients"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])

# uvicorn 실행 코드
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)