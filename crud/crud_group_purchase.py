from typing import List, Optional, Dict
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from crud.base import CRUDBase
from models.models import GroupPurchase, GroupPurchaseParticipant, User
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
        self, db: AsyncSession, *, group_purchase_id: int, current_user: User
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
                    GroupPurchaseParticipant.username == current_user.username
                )
            )
        )
        if participant_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User already joined this group purchase")
            
        # 새로운 참여자 추가
        new_participant = GroupPurchaseParticipant(
            username=current_user.username,
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

    async def get_group_purchase_with_participants(
        self, db: AsyncSession, *, group_purchase_id: int
    ) -> Dict:
        # 공동구매 정보 조회
        result = await db.execute(
            select(GroupPurchase).where(GroupPurchase.id == group_purchase_id)
        )
        group_purchase = result.scalar_one_or_none()
        
        if not group_purchase:
            raise HTTPException(status_code=404, detail="Group purchase not found")
        
        # 참여자 정보 조회
        participants_result = await db.execute(
            select(GroupPurchaseParticipant, User)
            .join(User, GroupPurchaseParticipant.username == User.username)
            .where(GroupPurchaseParticipant.group_buy_id == group_purchase_id)
        )
        
        participants = []
        for participant, user in participants_result:
            participants.append({
                "id": participant.id,
                "username": user.username,
                "email": user.email,
                "joined_at": participant.joined_at
            })
        
        return {
            "id": group_purchase.id,
            "title": group_purchase.title,
            "description": group_purchase.description,
            "price": group_purchase.price,
            "max_participants": group_purchase.max_participants,
            "current_participants": group_purchase.current_participants,
            "status": group_purchase.status,
            "created_by": group_purchase.created_by,
            "end_date": group_purchase.end_date,
            "created_at": group_purchase.created_at,
            "updated_at": group_purchase.updated_at,
            "closed_at": group_purchase.closed_at,
            "participants_info": participants
        }

    async def delete_group_purchase(
        self, db: AsyncSession, *, group_purchase_id: int, current_user_id: int
    ) -> bool:
        """공동구매 삭제"""
        result = await db.execute(
            select(GroupPurchase).where(GroupPurchase.id == group_purchase_id)
        )
        group_purchase = result.scalar_one_or_none()
        
        if not group_purchase:
            raise HTTPException(status_code=404, detail="Group purchase not found")
        
        # 생성자만 삭제 가능
        if group_purchase.created_by != current_user_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to delete this group purchase"
            )
        
        # 이미 참여자가 있는 경우 삭제 불가
        if group_purchase.current_participants > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete group purchase with existing participants"
            )
        
        await db.delete(group_purchase)
        await db.commit()
        
        return True

group_purchase = CRUDGroupPurchase(GroupPurchase)
