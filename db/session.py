from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=50,         # 기본 연결 풀 크기 증가
    max_overflow=20,      # 추가 연결 허용 수 
    pool_timeout=90,      # 타임아웃 시간 늘리기
    pool_recycle=3600,    # 1시간마다 연결 재생성
    pool_pre_ping=True,   # 연결 상태 사전 확인
    echo=False,
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)