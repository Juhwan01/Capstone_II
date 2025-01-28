from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db, get_current_active_user
from crud.crud_group_purchase import group_purchase
from schemas.group_purchases import (
    GroupPurchase, 
    GroupPurchaseCreate, 
    GroupPurchaseUpdate
)
from models.models import User

router = APIRouter(prefix="/group-purchases", tags=["group-purchases"])

@router.post("/", response_model=GroupPurchase)
async def create_group_purchase(
    *,
    db: AsyncSession = Depends(get_async_db),
    group_purchase_in: GroupPurchaseCreate,
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 생성"""
    group_purchase_obj = await group_purchase.create_with_owner(
        db=db,
        obj_in=group_purchase_in,
        owner_id=current_user.id
    )
    return group_purchase_obj

@router.get("/", response_model=List[GroupPurchase])
async def list_group_purchases(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 목록 조회"""
    group_purchases = await group_purchase.get_multi(
        db=db,
        skip=skip,
        limit=limit
    )
    return group_purchases

@router.post("/{group_purchase_id}/join")
async def join_group_purchase(
    *,
    db: AsyncSession = Depends(get_async_db),
    group_purchase_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 참여"""
    group_purchase_obj = await group_purchase.join_group_purchase(
        db=db,
        group_purchase_id=group_purchase_id,
        user_id=current_user.id
    )
    return group_purchase_obj

@router.get("/{group_purchase_id}", response_model=GroupPurchase)
async def get_group_purchase(
    *,
    db: AsyncSession = Depends(get_async_db),
    group_purchase_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """공동구매 상세 조회"""
    group_purchase_obj = await group_purchase.get(db=db, id=group_purchase_id)
    if not group_purchase_obj:
        raise HTTPException(status_code=404, detail="Group purchase not found")
    return group_purchase_obj

