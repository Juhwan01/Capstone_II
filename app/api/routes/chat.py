from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from services.chat_service import ChatService
from schemas.chat import ChatBase, MessageCreate, MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db

router = APIRouter()



@router.post("/chats/", response_model=ChatBase)
async def create_chat(user1_id: int, user2_id: int, db: AsyncSession = Depends(get_db)):
    chat_service = ChatService(db)
    return await chat_service.create_chat(user1_id, user2_id)

@router.get("/chat/", response_model=list[ChatBase])
async def get_chats(user_id: int, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    return await chat_service.get_user_chats(user_id)

@router.post("/messages/", response_model=MessageResponse)
async def send_message(message: MessageCreate, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    return await chat_service.send_message(message)

# WebSocket 엔드포인트
@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    # 연결 수락
    await websocket.accept()
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")