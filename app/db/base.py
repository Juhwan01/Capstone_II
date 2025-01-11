from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

# Base 클래스 정의
class Base(AsyncAttrs, DeclarativeBase):
    pass
