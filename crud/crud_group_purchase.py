import traceback
from typing import List, Optional, Dict, Any
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime
from models.models import GroupPurchase, GroupPurchaseParticipant, User, Image, GroupPurchaseStatus
from schemas.group_purchases import GroupPurchaseCreate, GroupPurchaseUpdate, GroupPurchase as GroupPurchaseSchema
from services.s3_service import upload_images_to_s3, delete_images_from_s3

class CRUDGroupPurchase:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_group_purchase(
        self, 
        db: AsyncSession, 
        group_purchase_data: GroupPurchaseCreate,
        current_user: User,
        saving_price: float,
        image_urls: Optional[List[str]] = None
    ) -> GroupPurchase:
        """
        공동구매 생성 (이미지 포함)
        """
        try:
            # 공동구매 객체 생성
            db_obj = GroupPurchase(
                title=group_purchase_data.title,
                description=group_purchase_data.description,
                created_by=current_user.id,
                price=group_purchase_data.price,
                original_price=group_purchase_data.original_price,
                saving_price=saving_price,
                category=group_purchase_data.category,
                max_participants=group_purchase_data.max_participants,
                current_participants=1,  # 생성자는 자동 참여
                status=GroupPurchaseStatus.OPEN,
                end_date=group_purchase_data.end_date
            )
            self.db.add(db_obj)
            await self.db.flush()  # id 획득을 위한 flush
            
            # 이미지가 있다면 저장
            if image_urls:
                image_objects = []
                for url in image_urls:
                    image = Image(
                        group_purchase_id=db_obj.id, 
                        image_url=url
                    )
                    image_objects.append(image)
                    
                self.db.add_all(image_objects)
            
            # 참여자 추가 (생성자도 참여자가 됨)
            participant = GroupPurchaseParticipant(
                group_buy_id=db_obj.id,
                username=current_user.username
            )
            self.db.add(participant)
            
            await self.db.commit()
            await self.db.refresh(db_obj)
            
            # 이미지 포함하여 조회
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .where(GroupPurchase.id == db_obj.id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 공동구매 생성 중 오류 발생: {e}")
            raise e
    
    async def get(self, db: AsyncSession, id: int) -> Optional[GroupPurchase]:
        """
        공동구매 조회 (이미지 포함)
        """
        try:
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .options(selectinload(GroupPurchase.participants))
                .where(GroupPurchase.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            traceback.print_exc()
            print(f"🚨 공동구매 조회 중 오류 발생: {e}")
            return None
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[GroupPurchase]:
        """
        공동구매 목록 조회 (이미지 포함)
        """
        try:
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            traceback.print_exc()
            print(f"🚨 공동구매 목록 조회 중 오류 발생: {e}")
            return []
    
    async def update_group_purchase(
        self, 
        db: AsyncSession, 
        group_purchase_id: int, 
        current_user: User, 
        obj_in: GroupPurchaseUpdate,
        image_urls: Optional[List[str]] = None
    ) -> Optional[GroupPurchase]:
        """
        공동구매 수정 (이미지 업데이트 포함)
        """
        try:
            # 기존 공동구매 조회
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .where(GroupPurchase.id == group_purchase_id)
            )
            db_obj = result.scalar_one_or_none()
            
            if not db_obj:
                return None
                
            # 권한 체크: 소유자만 수정 가능
            if db_obj.created_by != current_user.id:
                raise ValueError("Only the creator can update this group purchase")
                
            # 데이터 업데이트
            update_data = {k: v for k, v in obj_in.dict(exclude_unset=True).items() if v is not None}
            
            # price와 original_price 모두 변경된 경우 saving_price도 업데이트
            if "price" in update_data and "original_price" in update_data:
                update_data["saving_price"] = update_data["original_price"] - update_data["price"]
            elif "price" in update_data:
                update_data["saving_price"] = db_obj.original_price - update_data["price"]
            elif "original_price" in update_data:
                update_data["saving_price"] = update_data["original_price"] - db_obj.price
                
            # 데이터 업데이트
            for field, value in update_data.items():
                setattr(db_obj, field, value)
                
            # 이미지 변경이 있는 경우
            if image_urls is not None:
                # 기존 이미지 S3에서 삭제
                existing_images = [img.image_url for img in db_obj.images] if db_obj.images else []
                if existing_images:
                    await delete_images_from_s3(existing_images)
                
                # DB에서 기존 이미지 삭제
                await self.db.execute(
                    delete(Image).where(Image.group_purchase_id == group_purchase_id)
                )
                await self.db.flush()
                
                # 새 이미지 추가
                new_image_objects = [Image(group_purchase_id=db_obj.id, image_url=url) for url in image_urls]
                self.db.add_all(new_image_objects)
                
            await self.db.commit()
            await self.db.refresh(db_obj)
            
            # 이미지 포함하여 최신 정보 조회
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .where(GroupPurchase.id == group_purchase_id)
            )
            return result.scalar_one_or_none()
        
        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 공동구매 수정 중 오류 발생: {e}")
            raise e
    
    async def delete_group_purchase(
        self, 
        db: AsyncSession, 
        group_purchase_id: int, 
        current_user: User
    ) -> Dict[str, Any]:
        """
        공동구매 삭제 (S3 이미지 삭제)
        """
        try:
            # 기존 공동구매 조회 (이미지 포함)
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .where(GroupPurchase.id == group_purchase_id)
            )
            db_obj = result.scalar_one_or_none()
            
            if not db_obj:
                return {"error": "Group purchase not found"}
                
            # 권한 체크: 소유자만 삭제 가능
            if db_obj.created_by != current_user.id:
                return {"error": "Only the creator can delete this group purchase"}
                
            # 이미지 URL 추출
            image_urls = [img.image_url for img in db_obj.images] if db_obj.images else []
            
            # DB에서 공동구매 삭제 (이미지는 cascade로 자동 삭제)
            await self.db.delete(db_obj)
            await self.db.commit()
            
            # S3에서 이미지 삭제
            if image_urls:
                await delete_images_from_s3(image_urls)
                
            return {"message": "Group purchase and images successfully deleted"}
            
        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 공동구매 삭제 중 오류 발생: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    async def join_group_purchase(
        self, 
        db: AsyncSession, 
        group_purchase_id: int, 
        current_user: User
    ) -> Dict[str, Any]:
        """
        공동구매 참여
        """
        try:
            # 공동구매 존재 확인
            result = await self.db.execute(
                select(GroupPurchase).where(GroupPurchase.id == group_purchase_id)
            )
            db_obj = result.scalar_one_or_none()
            
            if not db_obj:
                return {"error": "Group purchase not found"}
                
            # 공동구매가 이미 마감된 경우
            if db_obj.status != GroupPurchaseStatus.OPEN:
                return {"error": "This group purchase is already closed"}
                
            # 참여자 수 확인
            if db_obj.current_participants >= db_obj.max_participants:
                return {"error": "This group purchase is already full"}
                
            # 이미 참여 중인지 확인
            participant_result = await self.db.execute(
                select(GroupPurchaseParticipant).where(
                    GroupPurchaseParticipant.group_buy_id == group_purchase_id,
                    GroupPurchaseParticipant.username == current_user.username
                )
            )
            existing_participant = participant_result.scalar_one_or_none()
            
            if existing_participant:
                return {"error": "You are already participating in this group purchase"}
                
            # 참여자 추가
            participant = GroupPurchaseParticipant(
                group_buy_id=group_purchase_id,
                username=current_user.username
            )
            self.db.add(participant)
            
            # 참여자 수 증가
            db_obj.current_participants += 1
            
            # 참여자 수가 최대에 도달하면 상태 변경
            if db_obj.current_participants >= db_obj.max_participants:
                db_obj.status = GroupPurchaseStatus.CLOSED
                db_obj.closed_at = datetime.utcnow()
                
            await self.db.commit()
            await self.db.refresh(db_obj)
            
            # 최신 정보로 조회
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .options(selectinload(GroupPurchase.participants))
                .where(GroupPurchase.id == group_purchase_id)
            )
            return {"group_purchase": result.scalar_one_or_none()}
            
        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 공동구매 참여 중 오류 발생: {e}")
            return {"error": f"Unexpected error: {str(e)}"}
        
    async def leave_group_purchase(
        self, 
        db: AsyncSession, 
        group_purchase_id: int, 
        current_user: User
    ) -> Dict[str, Any]:
        """
        공동구매 참여 취소
        """
        try:
            # 공동구매 존재 확인
            result = await self.db.execute(
                select(GroupPurchase).where(GroupPurchase.id == group_purchase_id)
            )
            db_obj = result.scalar_one_or_none()
            
            if not db_obj:
                return {"error": "Group purchase not found"}
                
            # 소유자는 참여 취소 불가
            if db_obj.created_by == current_user.id:
                return {"error": "The creator cannot leave the group purchase"}
                
            # 참여자 확인
            participant_result = await self.db.execute(
                select(GroupPurchaseParticipant).where(
                    GroupPurchaseParticipant.group_buy_id == group_purchase_id,
                    GroupPurchaseParticipant.username == current_user.username
                )
            )
            participant = participant_result.scalar_one_or_none()
            
            if not participant:
                return {"error": "You are not participating in this group purchase"}
                
            # 참여 취소
            await self.db.delete(participant)
            
            # 참여자 수 감소
            db_obj.current_participants -= 1
            
            # 상태가 CLOSED였다면 다시 OPEN으로 변경
            if db_obj.status == GroupPurchaseStatus.CLOSED and db_obj.current_participants < db_obj.max_participants:
                db_obj.status = GroupPurchaseStatus.OPEN
                db_obj.closed_at = None
                
            await self.db.commit()
            await self.db.refresh(db_obj)
            
            # 최신 정보로 조회
            result = await self.db.execute(
                select(GroupPurchase)
                .options(selectinload(GroupPurchase.images))
                .where(GroupPurchase.id == group_purchase_id)
            )
            return {"group_purchase": result.scalar_one_or_none()}
            
        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 공동구매 참여 취소 중 오류 발생: {e}")
            return {"error": f"Unexpected error: {str(e)}"}

# 인스턴스 생성 (FastAPI 의존성 주입용)
group_purchase = CRUDGroupPurchase(None)