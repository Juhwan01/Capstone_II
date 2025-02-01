from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API 설정
    PROJECT_NAME: str = "Recipe Recommendation System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 보안 설정
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # 데이터베이스 설정
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()