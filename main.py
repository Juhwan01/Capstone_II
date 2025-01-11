from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, users, recipes
from core.config import settings
from db.base import Base
from db.session import engine


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(recipes.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)