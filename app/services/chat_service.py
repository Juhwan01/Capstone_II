from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.chat import Chat, Message
from schemas.chat import MessageCreate
from models.user import User


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chat(self, user1_id: int, user2_id: int):
        # 사용자 ID 검증
        user1 = await self.db.execute(select(User).filter(User.id == user1_id))
        user1 = user1.scalars().first()

        user2 = await self.db.execute(select(User).filter(User.id == user2_id))
        user2 = user2.scalars().first()

        if not user1 or not user2:
            raise HTTPException(status_code=404, detail="One or both users not found")

        # 채팅 생성
        chat = Chat(user1_id=user1_id, user2_id=user2_id)
        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)

        # 관계 필드 즉시 로드
        chat_with_users = await self.db.execute(
            select(Chat)
            .options(joinedload(Chat.user1), joinedload(Chat.user2))
            .filter(Chat.id == chat.id)
        )
        return chat_with_users.scalars().first()

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
