from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API 설정
    PROJECT_NAME: str = "Recipe Recommendation System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 보안 설정
    SECRET_KEY: str = "your-super-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 데이터베이스 설정
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "3321"
    POSTGRES_SERVER: str = "localhost:5432"
    POSTGRES_DB: str = "postgres"
    
    # OCR 및 OpenAI 설정 추가
    CLOVA_OCR_API_URL: str = ""
    CLOVA_OCR_SECRET_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()