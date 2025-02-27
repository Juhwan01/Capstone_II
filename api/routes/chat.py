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
        # 각 연결에 email 정보를 함께 저장하기 위해 튜플 리스트로 변경
        self.active_connections: dict[int, list[tuple[WebSocket, str]]] = {}
    
    async def connect(self, room_id: int, websocket: WebSocket, email: str):
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append((websocket, email))
    
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

    async def broadcast(self, room_id: int, message: str, sender_email: str = None):
        if room_id in self.active_connections:
            for connection, email in self.active_connections[room_id]:
                # sender_email이 제공되었으면 발신자를 제외하고 전송
                if sender_email is None or email != sender_email:
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

# WebSocket 핸들러 수정
@router.websocket("/ws/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: int, db: AsyncSession = Depends(get_async_db)):
    """특정 채팅방에서 실시간 메시지 송수신"""
    print(f"웹소켓 연결 시도: 채팅방 {room_id}")
    
    # 먼저 연결을 수락
    await websocket.accept()
    print(f"웹소켓 연결 수락됨: 채팅방 {room_id}")
    
    # 쿼리 파라미터에서 토큰과 user_id 추출
    token = websocket.query_params.get("token")
    user_id_param = websocket.query_params.get("user_id")
    
    if not token:
        print(f"토큰 없음: 채팅방 {room_id}")
        await websocket.close()
        return
    
    try:
        # 토큰 검증
        print(f"토큰 검증 시작: 채팅방 {room_id}")
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        user_id = payload.get("user_id") or user_id_param
        print(f"토큰 검증 완료: 채팅방 {room_id}, 이메일: {email}, 사용자 ID: {user_id}")
        
        # 토큰 만료 확인
        if datetime.fromtimestamp(payload.get("exp")) < datetime.utcnow():
            print(f"토큰 만료됨: 채팅방 {room_id}")
            await websocket.close()
            return
            
        # 이메일은 필수, user_id가 없어도 진행
        if not email:
            print(f"이메일 없음: 채팅방 {room_id}")
            await websocket.close()
            return
        
        # 연결 상태 메시지 전송
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "room_id": room_id
        }))
        
        # 매니저에 연결 추가
        await manager.connect(room_id, websocket, email)
        print(f"매니저에 연결 추가됨: 채팅방 {room_id}")
        
        try:
            # 채팅 서비스 인스턴스 생성 및 채팅 내역 불러오기
            try:
                chat_service = CRUDchat(db)
                print(f"채팅 내역 로드 시작: 채팅방 {room_id}")
                chat_history = await chat_service.get_chat_messages(room_id)
                print(f"채팅 내역 로드 완료: {len(chat_history)}개 메시지")
                
                # 이전 채팅 내역을 클라이언트에게 전송
                history_data = {
                    "type": "history",
                    "messages": chat_history
                }
                await websocket.send_text(json.dumps(history_data))
                print(f"채팅 내역 전송 완료: 채팅방 {room_id}")
            except Exception as e:
                print(f"채팅 내역 로드 실패: {str(e)}")
                # 내역 로드 실패 메시지 전송
                await websocket.send_text(json.dumps({
                    "type": "history_error",
                    "message": "채팅 내역을 불러오는 중 오류가 발생했습니다."
                }))
            
            # 메시지 수신 루프
            while True:
                print(f"메시지 수신 대기: 채팅방 {room_id}")
                data = await websocket.receive_text()
                print(f"메시지 수신됨: 채팅방 {room_id}")
                
                try:
                    message_data = json.loads(data)
                    
                    # 메시지 타입이 'chat'인 경우 데이터베이스에 저장
                    if message_data.get("type") == "chat" and user_id:
                        try:
                            print(f"메시지 저장 시작: 채팅방 {room_id}")
                            message_create = MessageCreate(
                                content=message_data.get("content"),
                                sender_id=user_id,
                                chat_id=room_id
                            )
                            await chat_service.send_message(message_create)
                            print(f"메시지 저장 완료: 채팅방 {room_id}")
                        except Exception as e:
                            print(f"메시지 저장 실패: {str(e)}")
                    
                    # 메시지를 발신자를 제외한 모든 사용자에게 전달
                    print(f"메시지 브로드캐스트 시작: 채팅방 {room_id}")
                    await manager.broadcast(room_id, data, email)
                    print(f"메시지 브로드캐스트 완료: 채팅방 {room_id}")
                    
                except json.JSONDecodeError:
                    print(f"JSON 파싱 실패: 채팅방 {room_id}")
                    # 일반 텍스트인 경우 그대로 전달
                    await manager.broadcast(room_id, data, email)
                
        except WebSocketDisconnect:
            # 연결 종료 시 매니저에서 제거
            print(f"웹소켓 연결 종료: 채팅방 {room_id}")
            manager.disconnect(room_id, websocket)
            
    except JWTError as e:
        print(f"JWT 오류: 채팅방 {room_id}, {str(e)}")
        await websocket.close()
    except Exception as e:
        print(f"예상치 못한 오류: 채팅방 {room_id}, {str(e)}")
        await websocket.close()