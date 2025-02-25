from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.models import Chat, Message, Sale, User
from schemas.chat import MessageCreate



class CRUDchat:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chat(self, buyer_id: int, seller_id: int, item_id: int) -> Chat:
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
            select(Chat)
            .options(joinedload(Chat.buyer), joinedload(Chat.seller), joinedload(Chat.item), joinedload(Chat.messages))
            .filter(Chat.buyer_id == buyer_id, Chat.seller_id == seller_id, Chat.item_id == item_id)
        )
        existing_chat = existing_chat.scalars().first()

        if existing_chat:
            return existing_chat  # ✅ 기존 채팅방 반환

        # 새 채팅방 생성
        chat = Chat(buyer_id=buyer_id, seller_id=seller_id, item_id=item_id)
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)

        # ✅ 즉시 로딩된 상태로 다시 조회 후 반환 (이게 핵심)
        chat_with_relations = await self.db.execute(
            select(Chat)
            .options(joinedload(Chat.buyer), joinedload(Chat.seller), joinedload(Chat.item), joinedload(Chat.messages))
            .filter(Chat.id == chat.id)
        )
        return chat_with_relations.scalars().first()


    async def get_user_chats(self, user_id: int) -> list[Chat]:
        """특정 사용자가 참여한 모든 채팅방 조회"""
        result = await self.db.execute(
            select(Chat)
            .distinct()
            .options(joinedload(Chat.buyer), joinedload(Chat.seller), joinedload(Chat.item))  # ✅ 즉시 로딩 추가
            .filter((Chat.buyer_id == user_id) | (Chat.seller_id == user_id))
        )
        return result.scalars().unique().all()


    async def send_message(self, message: MessageCreate) -> Message:
        """채팅 메시지 저장"""
        new_message = Message(**message.dict())
        self.db.add(new_message)
        await self.db.commit()
        await self.db.refresh(new_message)
        return new_message