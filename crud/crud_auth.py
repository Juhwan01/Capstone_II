from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.security import get_password_hash, verify_password
from models.models import User
from schemas.auth import UserCreate

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User).filter(User.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(
        select(User).filter(User.username == username)
    )
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user