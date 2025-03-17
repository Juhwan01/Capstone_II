from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.security import get_password_hash, verify_password
from models.models import User
from schemas.auth import UserCreate,UserUpdate
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

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """ID로 사용자 조회"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

async def update_user_info(
    db: AsyncSession, user_id: int, update_data: UserUpdate
) -> Optional[User]:
    """사용자 정보 업데이트"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    # 필드 업데이트
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # 이메일, 아이디, 닉네임 중복 검사
    if 'email' in update_dict and update_dict['email'] != user.email:
        if await get_user_by_email(db, update_dict['email']):
            raise ValueError("Email already registered")
            
    if 'username' in update_dict and update_dict['username'] != user.username:
        if await get_user_by_username(db, update_dict['username']):
            raise ValueError("Username already taken")
            
    if 'nickname' in update_dict and update_dict['nickname'] != user.nickname:
        if await get_user_by_nickname(db, update_dict['nickname']):
            raise ValueError("Nickname already taken")
    
    # 비밀번호가 있으면 해시 처리
    if 'password' in update_dict:
        user.hashed_password = get_password_hash(update_dict.pop('password'))
    
    # 사용자 객체 업데이트
    for field, value in update_dict.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    # 변경사항 저장
    await db.commit()
    await db.refresh(user)
    return user