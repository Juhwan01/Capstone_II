from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from models.models import GroupChatroom, GroupChatMessage, GroupChatParticipant, GroupPurchase, User
from schemas.group_chat import GroupChatroomCreate, GroupChatMessageCreate


async def create_chatroom(db: AsyncSession, group_purchase_id: int) -> GroupChatroom:
    """그룹 구매에 대한 채팅방 생성"""
    # 먼저 그룹 구매가 존재하는지 확인
    result = await db.execute(select(GroupPurchase).filter(GroupPurchase.id == group_purchase_id))
    group_purchase = result.scalars().first()
    
    if not group_purchase:
        raise HTTPException(status_code=404, detail="해당 그룹 구매를 찾을 수 없습니다.")
    
    # 이미 채팅방이 존재하는지 확인
    existing_chatroom = await db.execute(
        select(GroupChatroom).filter(GroupChatroom.group_purchase_id == group_purchase_id)
    )
    existing_chatroom = existing_chatroom.scalars().first()
    
    if existing_chatroom:
        return existing_chatroom
    
    # 채팅방 생성
    chatroom = GroupChatroom(group_purchase_id=group_purchase_id)
    db.add(chatroom)
    await db.commit()
    await db.refresh(chatroom)
    
    # 관계형 데이터와 함께 채팅방 반환
    result = await db.execute(
        select(GroupChatroom)
        .options(joinedload(GroupChatroom.group_purchase))
        .filter(GroupChatroom.id == chatroom.id)
    )
    return result.scalars().first()


async def get_chatroom(db: AsyncSession, chatroom_id: int) -> GroupChatroom:
    """채팅방 ID로 채팅방 조회"""
    result = await db.execute(
        select(GroupChatroom)
        .options(joinedload(GroupChatroom.group_purchase))
        .filter(GroupChatroom.id == chatroom_id)
    )
    return result.scalars().first()


async def get_chatroom_by_group_purchase(db: AsyncSession, group_purchase_id: int) -> GroupChatroom:
    """그룹 구매 ID로 채팅방 조회"""
    result = await db.execute(
        select(GroupChatroom)
        .options(joinedload(GroupChatroom.group_purchase))
        .filter(GroupChatroom.group_purchase_id == group_purchase_id)
    )
    return result.scalars().first()


async def add_chat_participant(db: AsyncSession, chatroom_id: int, user_id: int) -> GroupChatParticipant:
    """채팅방에 참가자 추가"""
    # 채팅방 존재 확인
    chatroom = await get_chatroom(db, chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    # 사용자 존재 확인
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 이미 참가자인지 확인
    participant_result = await db.execute(
        select(GroupChatParticipant)
        .filter(
            GroupChatParticipant.chatroom_id == chatroom_id,
            GroupChatParticipant.user_id == user_id
        )
    )
    existing_participant = participant_result.scalars().first()
    
    if existing_participant:
        return existing_participant
    
    # 새 참가자 추가
    participant = GroupChatParticipant(chatroom_id=chatroom_id, user_id=user_id)
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    return participant


async def create_chat_message(db: AsyncSession, chat_message: GroupChatMessageCreate) -> GroupChatMessage:
    """채팅 메시지 저장"""
    # 채팅방 존재 확인
    chatroom = await get_chatroom(db, chat_message.chatroom_id)
    if not chatroom:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    
    # 사용자 존재 확인
    user_result = await db.execute(select(User).filter(User.id == chat_message.sender_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 메시지 생성
    # crud/crud_group_chat.py에서
    db_message = GroupChatMessage(
    chatroom_id=chat_message.chatroom_id,
    sender_id=chat_message.sender_id,
    content=chat_message.content  # message -> content로 변경
        )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


async def get_chat_messages(db: AsyncSession, chatroom_id: int, limit: int = 100) -> list[GroupChatMessage]:
    """채팅방의 메시지 이력 조회"""
    try:
        # 채팅방 존재 확인
        chatroom = await get_chatroom(db, chatroom_id)
        if not chatroom:
            raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
        
        # 메시지 조회 (시간순 정렬)
        result = await db.execute(
            select(GroupChatMessage)
            .options(joinedload(GroupChatMessage.sender))
            .filter(GroupChatMessage.chatroom_id == chatroom_id)
            .order_by(GroupChatMessage.timestamp)
            .limit(limit)
        )
        
        return result.scalars().all()
    except Exception as e:
        print(f"채팅 메시지 조회 중 오류: {str(e)}")
        # 오류가 발생해도 빈 리스트 반환하여 연결이 끊어지지 않도록 함
        return []


async def get_chatroom_participants(db: AsyncSession, chatroom_id: int) -> list[GroupChatParticipant]:
    """채팅방 참가자 목록 조회"""
    result = await db.execute(
        select(GroupChatParticipant)
        .options(joinedload(GroupChatParticipant.user))
        .filter(GroupChatParticipant.chatroom_id == chatroom_id)
    )
    return result.scalars().all()


async def remove_chat_participant(db: AsyncSession, chatroom_id: int, user_id: int) -> bool:
    """채팅방에서 참가자 제거"""
    participant_result = await db.execute(
        select(GroupChatParticipant)
        .filter(
            GroupChatParticipant.chatroom_id == chatroom_id,
            GroupChatParticipant.user_id == user_id
        )
    )
    participant = participant_result.scalars().first()
    
    if not participant:
        return False
    
    await db.delete(participant)
    await db.commit()
    return True