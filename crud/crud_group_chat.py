from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.models import GroupChatroom, GroupChatMessage, GroupChatParticipant
from schemas.group_chat import GroupChatroomCreate, GroupChatMessageCreate

async def create_chatroom(db: AsyncSession, group_purchase_id: int):
    chatroom = GroupChatroom(group_purchase_id=group_purchase_id)
    db.add(chatroom)
    await db.commit()  # ✅ 비동기 커밋
    await db.refresh(chatroom)
    return chatroom

async def get_chatroom(db: AsyncSession, group_purchase_id: int):
    result = await db.execute(select(GroupChatroom).filter(GroupChatroom.group_purchase_id == group_purchase_id))
    return result.scalars().first()

async def add_chat_participant(db: AsyncSession, chatroom_id: int, user_id: int):
    participant = GroupChatParticipant(chatroom_id=chatroom_id, user_id=user_id)
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    return participant

async def create_chat_message(db: AsyncSession, chat_message: GroupChatMessageCreate):
    db_message = GroupChatMessage(**chat_message.dict())
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_chat_messages(db: AsyncSession, chatroom_id: int):
    result = await db.execute(select(GroupChatMessage).filter(GroupChatMessage.chatroom_id == chatroom_id))
    return result.scalars().all()
