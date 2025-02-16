from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

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
    
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str 
    AWS_S3_BUCKET_NAME: str 

  


    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()