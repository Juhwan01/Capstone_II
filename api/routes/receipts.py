from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db, get_current_active_user
from services.receipt_service import ReceiptService
from models.models import User
from datetime import datetime
from typing import Dict, Any, List
from schemas.receipts import TempReceiptUpdate, IngredientUpdate
from pydantic import BaseModel

router = APIRouter(prefix="/receipts", tags=["receipts"])

class ConfirmItemBatch(BaseModel):
    temp_id: int
    category: str
    expiry_date: datetime

@router.post("/upload")
async def upload_receipt(
    *,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """영수증 이미지를 업로드하고 분석하여 임시 저장합니다."""
    receipt_service = ReceiptService()
    analyzed_items = await receipt_service.analyze_receipt(file, db)
    
    return {
        "message": "영수증이 성공적으로 분석되었습니다. 각 상품의 카테고리와 유통기한을 입력해주세요.",
        "items": analyzed_items
    }

@router.delete("/temp/{temp_id}")
async def delete_temp_item(
    temp_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """임시 저장된 상품을 삭제"""
    receipt_service = ReceiptService()
    await receipt_service.delete_temp_item(db, temp_id)
    
    return {
        "message": "상품이 성공적으로 삭제되었습니다."
    }

@router.put("/temp/{temp_id}")
async def update_temp_receipt(
    temp_id: int,
    update_data: TempReceiptUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """임시 저장된 영수증 데이터 수정"""
    receipt_service = ReceiptService()
    updated_item = await receipt_service.update_temp_receipt(
        db=db,
        temp_id=temp_id,
        update_data=update_data,
        user_id=current_user.id
    )
    return updated_item

@router.put("/ingredients/{ingredient_id}")
async def update_ingredient(
    ingredient_id: int,
    update_data: IngredientUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """저장된 식재료 데이터 수정"""
    receipt_service = ReceiptService()
    updated_ingredient = await receipt_service.update_ingredient(
        db=db,
        ingredient_id=ingredient_id,
        update_data=update_data,
        user_id=current_user.id
    )
    return updated_ingredient

@router.get("/ingredients/my")
async def get_my_ingredients(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """사용자의 식재료 목록 조회"""
    receipt_service = ReceiptService()
    ingredients = await receipt_service.get_user_ingredients(db, current_user.id)
    return ingredients

@router.post("/confirm-batch")
async def confirm_items_batch(
    items: List[ConfirmItemBatch],
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """여러 임시 저장 상품을 한 번에 ingredients 테이블로 이동"""
    receipt_service = ReceiptService()
    ingredients = []
    
    for item in items:
        ingredient = await receipt_service.save_to_ingredients(
            db,
            item.temp_id,
            item.category,
            item.expiry_date,
            current_user.id
        )
        ingredients.append({
            "id": ingredient.id,
            "name": ingredient.name,
            "category": ingredient.category,
            "expiry_date": ingredient.expiry_date,
            "amount": ingredient.amount,
            "user_id": ingredient.user_id
        })
    
    return {
        "message": "상품들이 성공적으로 저장되었습니다.",
        "ingredients": ingredients
    } 