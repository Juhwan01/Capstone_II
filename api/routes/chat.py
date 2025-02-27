from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from models.models import Message
from schemas.chat import ChatBase, ChatCreate, ChatQuery, MessageCreate, MessageResponse
from crud.crud_chat import CRUDchat
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
        self.active_connections: dict[int, list[tuple[WebSocket, str]]] = {}
    
    async def connect(self, room_id: int, websocket: WebSocket, user_email: str):
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append((websocket, user_email))
    
    def disconnect(self, room_id: int, websocket: WebSocket):
        if room_id in self.active_connections:
            # 해당 웹소켓 연결 찾아서 제거
            self.active_connections[room_id] = [
                conn for conn in self.active_connections[room_id] 
                if conn[0] != websocket
            ]
            # 채팅방에 아무도 없으면 채팅방 제거
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: str, sender_email: str):
        """
        메시지를 보낸 사용자를 제외한 모든 연결된 클라이언트에게 메시지 전송
        """
        if room_id in self.active_connections:
            for connection, user_email in self.active_connections[room_id]:
                # 발신자를 제외한 사용자에게만 메시지 전송
                if user_email != sender_email:
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

async def get_chat_messages(db: AsyncSession, room_id: int, limit: int = 100) -> list[dict]:
    """
    특정 채팅방의 최근 메시지 내역을 불러오는 함수
    
    Args:
        db: 데이터베이스 세션
        room_id: 채팅방 ID
        limit: 불러올 메시지 개수 (기본 100개)
        
    Returns:
        최근 메시지 목록 (시간순 정렬)
    """
    # Message 모델의 필드에 맞게 조회
    query = select(Message).where(Message.chat_id == room_id).order_by(Message.timestamp).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # 메시지를 JSON 직렬화 가능한 형태로 변환
    message_list = []
    for msg in messages:
        message_list.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "chat_id": msg.chat_id
        })
        
    return message_list

@router.websocket("/ws/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: int, db: AsyncSession = Depends(get_async_db)):
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
        user_id = payload.get("user_id")  # 토큰에 user_id가 포함되어 있다고 가정
        
        # 토큰 만료 확인
        if datetime.fromtimestamp(payload.get("exp")) < datetime.utcnow():
            await websocket.close()
            return
            
        if not email or not user_id:
            await websocket.close()
            return
        
        # 채팅 서비스 인스턴스 생성
        chat_service = CRUDchat(db)
        
        # 이전 채팅 내역 불러오기 (별도 함수 사용)
        chat_history = await get_chat_messages(db, room_id)
        
        # 이전 채팅 내역을 먼저 클라이언트에게 전송
        history_data = {
            "type": "history",
            "messages": chat_history
        }
        await websocket.send_text(json.dumps(history_data))
        
        # 매니저에 연결 추가 (이메일 정보도 함께 저장)
        await manager.connect(room_id, websocket, email)
        
        try:
            while True:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_text()
                
                # JSON 형태로 데이터가 오는 경우 파싱하여 처리
                try:
                    message_data = json.loads(data)
                    
                    # 메시지 타입이 'chat'인 경우 데이터베이스에 저장
                    if message_data.get("type") == "chat":
                        # 데이터베이스에 메시지 저장
                        message_create = MessageCreate(
                            content=message_data.get("content"),
                            sender_id=user_id,
                            chat_id=room_id
                            # timestamp는 DB에서 자동으로 설정됨
                        )
                        await chat_service.send_message(message_create)
                    
                    # 메시지를 발신자를 제외한 모든 사용자에게 전달
                    await manager.broadcast(room_id, data, email)
                    
                except json.JSONDecodeError:
                    # 일반 텍스트인 경우 그대로 전달
                    await manager.broadcast(room_id, data, email)
                
        except WebSocketDisconnect:
            # 연결 종료 시 매니저에서 제거
            manager.disconnect(room_id, websocket)
            print(f"채팅방 {room_id}: 클라이언트 연결 종료")
            
    except JWTError:
        await websocket.close()