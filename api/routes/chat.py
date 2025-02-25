from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from crud.crud_chat import CRUDchat
from schemas.chat import ChatBase, ChatCreate, ChatQuery, MessageCreate, MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/chats/", response_model=ChatBase)
async def create_chat(chat_data: ChatCreate, db: AsyncSession = Depends(get_async_db)):
    """구매자가 채팅을 시작하면 기존 채팅방을 찾고 없으면 생성"""
    chat_service = CRUDchat(db)
    return await chat_service.create_chat(chat_data.buyer_id, chat_data.seller_id, chat_data.item_id)

@router.get("/chats/", response_model=list[ChatBase])
async def get_chats(chat_query: ChatQuery, db: AsyncSession = Depends(get_async_db)):
    """사용자가 참여한 모든 채팅방을 조회"""
    chat_service = CRUDchat(db)
    return await chat_service.get_user_chats(chat_query.user_id)


@router.post("/messages/", response_model=MessageResponse)
async def send_message(message: MessageCreate, db: AsyncSession = Depends(get_async_db)):
    """메시지를 특정 채팅방에 저장"""
    chat_service = CRUDchat(db)
    return await chat_service.send_message(message)

@router.websocket("/ws/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: int):
    """특정 채팅방에서 실시간 메시지 송수신"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            # 특정 채팅방에서 메시지를 보내는 경우
            await websocket.send_text(f"Room {room_id} - Message: {data}")
    except WebSocketDisconnect:
        print(f"채팅방 {room_id}: 클라이언트 연결 종료")