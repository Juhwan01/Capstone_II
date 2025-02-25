from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from crud.crud_chat import CRUDchat
from schemas.chat import ChatBase, ChatCreate, ChatQuery, MessageCreate, MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db
from jose import JWTError, jwt
from core.config import settings

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/chats/", response_model=ChatBase)
async def create_chat(chat_data: ChatCreate, db: AsyncSession = Depends(get_async_db)):
    """구매자가 채팅을 시작하면 기존 채팅방을 찾고 없으면 생성"""
    chat_service = CRUDchat(db)
    chat = await chat_service.create_chat(chat_data.buyer_id, chat_data.seller_id, chat_data.item_id)

    return ChatBase.model_validate(chat)

@router.get("/chats/", response_model=list[ChatBase])
async def get_chats(user_id: int, db: AsyncSession = Depends(get_async_db)):
    """사용자가 참여한 모든 채팅방을 조회"""
    chat_service = CRUDchat(db)
    return await chat_service.get_user_chats(user_id)

@router.post("/messages/", response_model=MessageResponse)
async def send_message(message: MessageCreate, db: AsyncSession = Depends(get_async_db)):
    """메시지를 특정 채팅방에 저장"""
    chat_service = CRUDchat(db)
    return await chat_service.send_message(message)

@router.websocket("/ws/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: int):
    """특정 채팅방에서 실시간 메시지 송수신"""
    # 쿼리 파라미터에서 토큰 추출
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    try:
        # 토큰 검증
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        
        # 토큰 만료 확인
        if datetime.fromtimestamp(payload.get("exp")) < datetime.utcnow():
            await websocket.close(code=1008, reason="Token expired")
            return
            
        if not email:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # 여기서 이메일로 사용자 정보를 가져오거나 추가 검증을 할 수 있습니다
        # 예: 사용자가 채팅방에 접근할 권한이 있는지 확인
        
        await websocket.accept()
        
        try:
            while True:
                data = await websocket.receive_text()
                # 특정 채팅방에서 메시지를 보내는 경우
                await websocket.send_text(f"Room {room_id} - Message: {data}")
        except WebSocketDisconnect:
            print(f"채팅방 {room_id}: 클라이언트 연결 종료")
            
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")