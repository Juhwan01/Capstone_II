from typing import AsyncGenerator, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal
from core.config import settings
from crud import crud_auth
from schemas.auth import TokenData
from models.models import UserRole, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = await crud_auth.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_user_role(required_roles: List[UserRole]):
    async def role_checker(current_user: User = Security(get_current_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"해당 작업을 수행할 권한이 없습니다. 필요한 등급: {[role.value for role in required_roles]}"
            )
        return current_user
    return role_checker

# 각 권한 레벨에 대한 검사기
check_chef = check_user_role([UserRole.CHEF])
check_master_or_above = check_user_role([UserRole.CHEF, UserRole.MASTER])
check_expert_or_above = check_user_role([UserRole.CHEF, UserRole.MASTER, UserRole.EXPERT])