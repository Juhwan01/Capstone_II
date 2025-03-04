from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.models import Chat, Message, Sale, User
from schemas.chat import MessageCreate
from datetime import datetime


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
    async def get_chat_messages(self, room_id: int, limit: int = 100) -> list[dict]:
        """
        특정 채팅방의 최근 메시지 내역을 불러오는 함수
        
        Args:
            room_id: 채팅방 ID
            limit: 불러올 메시지 개수 (기본 100개)
            
        Returns:
            최근 메시지 목록 (시간순 정렬)
        """
        try:
            # timestamp 필드 사용
            query = select(Message).where(Message.chat_id == room_id).order_by(Message.timestamp).limit(limit)
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            # 메시지를 JSON 직렬화 가능한 형태로 변환
            message_list = []
            for msg in messages:
                try:
                    # None 체크만 수행
                    timestamp_str = msg.timestamp.isoformat() if msg.timestamp else None
                    
                    message_list.append({
                        "id": msg.id,
                        "sender_id": msg.sender_id,
                        "content": msg.content,
                        "timestamp": timestamp_str,
                        "chat_id": msg.chat_id
                    })
                except Exception as e:
                    print(f"메시지 변환 중 오류 (메시지 ID: {msg.id}): {str(e)}")
                    # 오류가 있는 경우 timestamp를 None으로 처리하고 계속 진행
                    message_list.append({
                        "id": msg.id,
                        "sender_id": msg.sender_id,
                        "content": msg.content,
                        "timestamp": None,
                        "chat_id": msg.chat_id
                    })
            
            return message_list
        except Exception as e:
            print(f"채팅 내역 조회 중 오류: {str(e)}")
            # 오류가 발생해도 빈 리스트 반환하여 연결이 끊어지지 않도록 함
            return []
