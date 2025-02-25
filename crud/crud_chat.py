from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.models import Chat, Message, Sale, User
from schemas.chat import MessageCreate


class CRUDchat:
    def __init__(self, db: AsyncSession):
        self.db = db

class CRUDchat:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chat(self, buyer_id: int, seller_id: int, item_id: int):
        """구매자가 채팅하기를 누르면 기존 채팅방이 있는지 확인 후 생성"""

        # 사용자 및 상품 확인
        buyer = await self.db.execute(select(User).filter(User.id == buyer_id))
        buyer = buyer.scalars().first()

        seller = await self.db.execute(select(User).filter(User.id == seller_id))
        seller = seller.scalars().first()

        sale_item = await self.db.execute(select(Sale).filter(Sale.id == item_id))
        sale_item = sale_item.scalars().first()

        if not buyer or not seller or not sale_item:
            raise HTTPException(status_code=404, detail="User or Sale Item not found")

        # 기존 채팅방 확인
        existing_chat = await self.db.execute(
            select(Chat).filter(
                Chat.buyer_id == buyer_id,
                Chat.seller_id == seller_id,
                Chat.item_id == item_id
            )
        )
        existing_chat = existing_chat.scalars().first()

        if existing_chat:
            return {"message": "채팅방이 이미 존재합니다.", "room_id": existing_chat.id}

        # 채팅방 생성
        chat = Chat(buyer_id=buyer_id, seller_id=seller_id, item_id=item_id)
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)

        return {"message": "새로운 채팅방이 생성되었습니다.", "room_id": chat.id}


    async def get_user_chats(self, user_id: int) -> list[Chat]:
        # 특정 사용자가 참여한 모든 채팅 조회
        result = await self.db.execute(
                select(Chat)
                .distinct()  # 중복된 Chat 객체 제거
                .options(joinedload(Chat.user1), joinedload(Chat.user2))
                .filter((Chat.user1_id == user_id) | (Chat.user2_id == user_id))
            )
        return result.scalars().unique().all()

    async def send_message(self, message: MessageCreate) -> Message:
        # 메시지 저장
        new_message = Message(**message.dict())
        self.db.add(new_message)
        await self.db.commit()
        await self.db.refresh(new_message)
        return new_message
