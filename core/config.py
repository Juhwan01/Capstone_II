from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API 설정
    PROJECT_NAME: str 
    VERSION: str
    API_V1_STR: str
    
    # 보안 설정
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # 데이터베이스 설정
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    
    # OCR 및 OpenAI 설정 추가
    CLOVA_OCR_API_URL: str
    CLOVA_OCR_SECRET_KEY: str
    OPENAI_API_KEY: str
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()