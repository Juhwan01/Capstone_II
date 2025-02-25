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

class ConnectionManager:
    def __init__(self):
        # room_id를 키로 사용하여 각 채팅방의 연결을 저장
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        if room_id in self.active_connections:
            # 해당 웹소켓 연결 찾아서 제거
            self.active_connections[room_id] = [
                conn for conn in self.active_connections[room_id] 
                if conn != websocket
            ]
            # 채팅방에 아무도 없으면 채팅방 제거
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

# 매니저 인스턴스 생성
manager = ConnectionManager()

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
    # 먼저 연결을 수락
    await websocket.accept()
    
    # 쿼리 파라미터에서 토큰 추출
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close()
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
            await websocket.close()
            return
            
        if not email:
            await websocket.close()
            return
        
        # 매니저에 연결 추가
        await manager.connect(room_id, websocket)
        
        try:
            while True:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                # 메시지를 그대로 전달 (수정 없이)
                await manager.broadcast(room_id, data)
        except WebSocketDisconnect:
            # 연결 종료 시 매니저에서 제거
            manager.disconnect(room_id, websocket)
            print(f"채팅방 {room_id}: 클라이언트 연결 종료")
            
    except JWTError:
        await websocket.close()