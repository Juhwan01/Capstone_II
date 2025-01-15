from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import ingredientRequest, Ingredient
from datetime import datetime


class RequestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(self, user_id: int, ingredient_id: int, request_type: str) -> dict:
        """새로운 요청 생성"""
        # 동일 식재료에 'Pending' 또는 'Completed' 상태 요청이 있는지 확인
        existing_request = await self.db.execute(
            select(IngredientRequest).where(
                (IngredientRequest.ingredient_id == ingredient_id) &
                (IngredientRequest.status.in_(["거래 중", "거래 완료"]))
            )
        )
        if existing_request.scalars().first():
            raise ValueError(f"Ingredient with ID {ingredient_id} is already in transaction or completed")

        # 새로운 요청 생성
        new_request = IngredientRequest(
            user_id=user_id,
            ingredient_id=ingredient_id,
            request_type=request_type,  # 요청 유형 추가
            status="거래 중"  # 기본 상태
        )
        self.db.add(new_request)
        await self.db.commit()
        await self.db.refresh(new_request)

        return {
            "request_id": new_request.id,
            "user_id": new_request.user_id,
            "ingredient_id": new_request.ingredient_id,
            "request_type": new_request.request_type,
            "status": new_request.status,
            "created_at": new_request.created_at
        }

    async def update_request_status(self, request_id: int, new_status: str) -> dict:
        """요청 상태를 업데이트"""
        # 요청 가져오기
        result = await self.db.execute(
            select(IngredientRequest).where(IngredientRequest.id == request_id)
        )
        request = result.scalars().first()

        if not request:
            raise ValueError(f"Request with ID {request_id} does not exist")
        if request.status == "Completed":
            raise ValueError(f"Request with ID {request_id} is already completed")

        # 상태 업데이트
        request.status = new_status
        await self.db.commit()

        return {
            "request_id": request.id,
            "ingredient_id": request.ingredient_id,
            "request_status": request.status,
            "updated_at": datetime.utcnow()
        }

    async def get_requests_by_user(self, user_id: int) -> list:
        """특정 사용자가 생성한 요청을 모두 조회합니다."""
        result = await self.db.execute(
            select(IngredientRequest).where(IngredientRequest.user_id == user_id)
        )
        requests = result.scalars().all()

        return [
            {
                "id": req.id,
                "ingredient_id": req.ingredient_id,
                "request_type": req.request_type,
                "status": req.status,
                "created_at": req.created_at
            }
            for req in requests
        ]
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import IngredientRequest, Ingredient
from datetime import datetime


class RequestService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(self, user_id: int, ingredient_id: int, request_type: str) -> dict:
        """새로운 요청 생성"""
        # 동일 식재료에 'Pending' 또는 'Completed' 상태 요청이 있는지 확인
        existing_request = await self.db.execute(
            select(IngredientRequest).where(
                (IngredientRequest.ingredient_id == ingredient_id) &
                (IngredientRequest.status.in_(["거래 중", "거래 완료"]))
            )
        )
        if existing_request.scalars().first():
            raise ValueError(f"Ingredient with ID {ingredient_id} is already in transaction or completed")

        # 새로운 요청 생성
        new_request = IngredientRequest(
            user_id=user_id,
            ingredient_id=ingredient_id,
            request_type=request_type,  # 요청 유형 추가
            status="거래 중"  # 기본 상태
        )
        self.db.add(new_request)
        await self.db.commit()
        await self.db.refresh(new_request)

        return {
            "request_id": new_request.id,
            "user_id": new_request.user_id,
            "ingredient_id": new_request.ingredient_id,
            "request_type": new_request.request_type,
            "status": new_request.status,
            "created_at": new_request.created_at
        }

    async def update_request_status(self, request_id: int, new_status: str) -> dict:
        """요청 상태를 업데이트"""
        # 요청 가져오기
        result = await self.db.execute(
            select(IngredientRequest).where(IngredientRequest.id == request_id)
        )
        request = result.scalars().first()

        if not request:
            raise ValueError(f"Request with ID {request_id} does not exist")
        if request.status == "Completed":
            raise ValueError(f"Request with ID {request_id} is already completed")

        # 상태 업데이트
        request.status = new_status
        await self.db.commit()

        return {
            "request_id": request.id,
            "ingredient_id": request.ingredient_id,
            "request_status": request.status,
            "updated_at": datetime.utcnow()
        }

    async def get_requests_by_user(self, user_id: int) -> list:
        """특정 사용자가 생성한 요청을 모두 조회합니다."""
        result = await self.db.execute(
            select(IngredientRequest).where(IngredientRequest.user_id == user_id)
        )
        requests = result.scalars().all()

        return [
            {
                "id": req.id,
                "ingredient_id": req.ingredient_id,
                "request_type": req.request_type,
                "status": req.status,
                "created_at": req.created_at
            }
            for req in requests
        ]
