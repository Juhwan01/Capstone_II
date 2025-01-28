from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from crud.base import CRUDBase
from models.models import GroupPurchase, GroupPurchaseParticipant
from schemas.group_purchases import GroupPurchaseCreate, GroupPurchaseUpdate, GroupPurchaseStatus
from datetime import datetime

class CRUDGroupPurchase(CRUDBase[GroupPurchase, GroupPurchaseCreate, GroupPurchaseUpdate]):
    async def create_with_owner(
        self, db: AsyncSession, *, obj_in: GroupPurchaseCreate, owner_id: int
    ) -> GroupPurchase:
        obj_in_data = obj_in.model_dump()
        db_obj = GroupPurchase(**obj_in_data, created_by=owner_id)  # status 제거
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def join_group_purchase(
        self, db: AsyncSession, *, group_purchase_id: int, user_id: int
    ) -> GroupPurchase:
        # 공동구매 정보 조회
        result = await db.execute(
            select(GroupPurchase).where(GroupPurchase.id == group_purchase_id)
        )
        group_purchase = result.scalar_one_or_none()
        
        if not group_purchase:
            raise HTTPException(status_code=404, detail="Group purchase not found")
            
        if group_purchase.current_participants >= group_purchase.max_participants:
            raise HTTPException(status_code=400, detail="Group purchase is already full")
            
        # 이미 참여한 사용자인지 확인
        participant_result = await db.execute(
            select(GroupPurchaseParticipant).where(
                and_(
                    GroupPurchaseParticipant.group_buy_id == group_purchase_id,
                    GroupPurchaseParticipant.user_id == user_id
                )
            )
        )
        if participant_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already joined this group purchase")
            
        # 새로운 참여자 추가
        new_participant = GroupPurchaseParticipant(
            user_id=user_id,
            group_buy_id=group_purchase_id
        )
        db.add(new_participant)
        
        # 참여자 수 증가 및 상태 업데이트
        group_purchase.current_participants += 1
        if group_purchase.current_participants >= group_purchase.max_participants:
            group_purchase.status = "completed"
            group_purchase.closed_at = datetime.utcnow()
            
        await db.commit()
        await db.refresh(group_purchase)
        
        return group_purchase

    async def update_participant_count_and_status(
        self, db: AsyncSession, group_purchase: GroupPurchase
    ):
        """참여자 수와 상태 업데이트"""
        group_purchase.current_participants += 1
        if group_purchase.current_participants >= group_purchase.max_participants:
            group_purchase.status = GroupPurchaseStatus.COMPLETED
        await db.commit()
        await db.refresh(group_purchase)

group_purchase = CRUDGroupPurchase(GroupPurchase)
