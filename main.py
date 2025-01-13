from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router
from db.base import Base
from db.session import engine

app = FastAPI(
    title="Recipe Recommendation System",
    description="Recipe recommendation system with user authentication",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)