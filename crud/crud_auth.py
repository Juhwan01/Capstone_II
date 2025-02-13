from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.security import get_password_hash, verify_password
from models.models import User
from schemas.auth import UserCreate
from models.models import UserRole
from fastapi import HTTPException

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    print("---------------------------------------------------")
    result = await db.execute(
        select(User).filter(User.email == email)
    )
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    print("---------------------------------------------------")
    result = await db.execute(
        select(User).filter(User.username == username)
    )
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def update_user_role(
    db: AsyncSession, user_id: int, trust_score: float
) -> Optional[User]:
    """Update user role based on trust score"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None

    # Update role based on trust score
    if trust_score >= 90:
        user.role = UserRole.CHEF
    elif trust_score >= 70:
        user.role = UserRole.MASTER
    elif trust_score >= 50:
        user.role = UserRole.EXPERT
    else:
        user.role = UserRole.NEWBIE

    user.trust_score = trust_score
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_nickname(db: AsyncSession, nickname: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.nickname == nickname)
    )
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    # Check if nickname is already taken
    if await get_user_by_nickname(db, user.nickname):
        raise HTTPException(
            status_code=400,
            detail="Nickname already registered"
        )
        
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        nickname=user.nickname,
        hashed_password=hashed_password,
        address_name=user.address_name,
        zone_no=user.zone_no,
        location_lat=user.location_lat,
        location_lon=user.location_lon
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user