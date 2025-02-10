from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_async_db
from core.security import create_access_token
from core.config import settings
from crud import crud_auth
from schemas.auth import Token, UserCreate, User
from schemas.users import UserProfileCreate
from crud.crud_user import user as crud_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=User)
async def register(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_in: UserCreate
):
    """Create new user with profile"""
    user = await crud_auth.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    user = await crud_auth.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
        
    user = await crud_auth.get_user_by_nickname(db, nickname=user_in.nickname)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Nickname already taken"
        )
    print("create_user 호출 전", user_in)
    user = await crud_auth.create_user(db, user_in)
    
    profile_in = UserProfileCreate()
    await crud_user.create_with_owner(
        db=db,
        obj_in=profile_in,
        owner_id=user.id
    )
    
    return user

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_async_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await crud_auth.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }