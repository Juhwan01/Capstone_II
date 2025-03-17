from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.dependencies import get_async_db
from models.models import GroupChatroom, GroupChatMessage, GroupChatParticipant, User
from schemas.group_chat import GroupChatroomCreate, GroupChatMessageCreate
from crud.crud_group_chat import (
    create_chatroom, 
    get_chatroom, 
    add_chat_participant,
    create_chat_message, 
    get_chat_messages
)
from jose import JWTError, jwt
from core.config import settings

router = APIRouter(prefix="/group-purchases", tags=["group-purchases"])

class GroupChatManager:
    def __init__(self):
        # 채팅방 ID를 키로 사용하여 각 그룹 채팅방의 연결을 저장
        # 각 연결에 email과 user_id 정보를 함께 저장하기 위해 튜플 리스트로 변경
        self.active_connections: dict[int, list[tuple[WebSocket, str, int]]] = {}
    
    async def connect(self, chatroom_id: int, websocket: WebSocket, email: str, user_id: int):
        if chatroom_id not in self.active_connections:
            self.active_connections[chatroom_id] = []
        self.active_connections[chatroom_id].append((websocket, email, user_id))
    
    def disconnect(self, chatroom_id: int, websocket: WebSocket):
        if chatroom_id in self.active_connections:
            # 해당 웹소켓 연결 찾아서 제거
            self.active_connections[chatroom_id] = [
                conn for conn in self.active_connections[chatroom_id] 
                if conn[0] != websocket
            ]
            # 채팅방에 아무도 없으면 채팅방 제거
            if not self.active_connections[chatroom_id]:
                del self.active_connections[chatroom_id]

    async def broadcast(self, chatroom_id: int, message: str, sender_email: str = None):
        if chatroom_id in self.active_connections:
            for connection, email, _ in self.active_connections[chatroom_id]:
                # sender_email이 제공되었으면 발신자를 제외하고 전송
                if sender_email is None or email != sender_email:
                    await connection.send_text(message)

# 그룹 채팅 매니저 인스턴스 생성
group_chat_manager = GroupChatManager()

@router.post("/chatrooms/", response_model=dict)
async def create_group_chatroom(group_purchase_id: int, db: AsyncSession = Depends(get_async_db)):
    """그룹 구매에 대한 채팅방 생성"""
    try:
        chatroom = await create_chatroom(db, group_purchase_id)
        return {
            "success": True,
            "chatroom_id": chatroom.id,
            "group_purchase_id": chatroom.group_purchase_id,
            "created_at": chatroom.created_at
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/chatrooms/{chatroom_id}/participants/", response_model=dict)
async def add_participant(chatroom_id: int, user_id: int, db: AsyncSession = Depends(get_async_db)):
    """채팅방에 참가자 추가"""
    try:
        participant = await add_chat_participant(db, chatroom_id, user_id)
        return {
            "success": True,
            "participant_id": participant.id,
            "user_id": participant.user_id,
            "chatroom_id": participant.chatroom_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/chatrooms/{chatroom_id}/messages/", response_model=list)
async def get_messages(chatroom_id: int, db: AsyncSession = Depends(get_async_db)):
    """채팅방의 메시지 이력 조회"""
    return await get_chat_messages(db, chatroom_id)

async def get_user_by_email(db: AsyncSession, email: str) -> User:
    """이메일로 사용자 조회"""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

@router.websocket("/ws/groupchat/{chatroom_id}")
async def group_chat(websocket: WebSocket, chatroom_id: int, db: AsyncSession = Depends(get_async_db)):
    """그룹 채팅 WebSocket 핸들러"""
    print(f"그룹 웹소켓 연결 시도: 채팅방 {chatroom_id}")
    
    # 먼저 연결을 수락
    await websocket.accept()
    print(f"그룹 웹소켓 연결 수락됨: 채팅방 {chatroom_id}")
    
    # 쿼리 파라미터에서 토큰과 user_id 추출
    token = websocket.query_params.get("token")
    user_id_param = websocket.query_params.get("user_id")
    
    if not token:
        print(f"토큰 없음: 그룹 채팅방 {chatroom_id}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "인증 토큰이 필요합니다."
        }))
        await websocket.close()
        return
    
    try:
        # 토큰 검증
        print(f"토큰 검증 시작: 그룹 채팅방 {chatroom_id}")
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        # user_id를 토큰 또는 쿼리 파라미터에서 가져오기
        user_id = payload.get("user_id") or user_id_param
        print(f"토큰 검증 완료: 그룹 채팅방 {chatroom_id}, 이메일: {email}, 사용자 ID: {user_id}")
        
        # 이메일로 사용자 ID 찾기 (토큰에 user_id가 없는 경우)
        if not user_id and email:
            user = await get_user_by_email(db, email)
            if user:
                user_id = str(user.id)
                print(f"이메일로 사용자 ID 찾음: {user_id}")
        
        # 토큰 만료 확인
        if datetime.fromtimestamp(payload.get("exp")) < datetime.utcnow():
            print(f"토큰 만료됨: 그룹 채팅방 {chatroom_id}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "인증 토큰이 만료되었습니다."
            }))
            await websocket.close()
            return
            
        # 이메일은 필수, user_id가 없으면 오류
        if not email:
            print(f"이메일 없음: 그룹 채팅방 {chatroom_id}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "인증 정보가 유효하지 않습니다."
            }))
            await websocket.close()
            return
        
        # user_id가 없으면 오류
        if not user_id:
            print(f"사용자 ID를 찾을 수 없음: 그룹 채팅방 {chatroom_id}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "사용자 ID를 찾을 수 없습니다. 다시 로그인해주세요."
            }))
            await websocket.close()
            return
        
        # 채팅방 존재 확인
        chatroom = await get_chatroom(db, chatroom_id)
        if not chatroom:
            print(f"채팅방이 존재하지 않음: 그룹 채팅방 {chatroom_id}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "채팅방이 존재하지 않습니다."
            }))
            await websocket.close()
            return
        
        # 연결 상태 메시지 전송
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "chatroom_id": chatroom_id
        }))
        
        # 매니저에 연결 추가
        await group_chat_manager.connect(chatroom_id, websocket, email, int(user_id))
        print(f"매니저에 연결 추가됨: 그룹 채팅방 {chatroom_id}")
        
        try:
            # 채팅방에 사용자 추가 (아직 참가자가 아니라면)
            try:
                await add_chat_participant(db, chatroom_id, int(user_id))
                print(f"사용자 {user_id}를 채팅방 {chatroom_id}에 추가됨")
            except Exception as e:
                # 이미 참가자일 경우 에러가 발생할 수 있으므로 무시
                print(f"참가자 추가 중 에러 (무시됨): {str(e)}")
            
            # 채팅 내역 불러오기
            try:
                print(f"채팅 내역 로드 시작: 그룹 채팅방 {chatroom_id}")
                chat_history = await get_chat_messages(db, chatroom_id)
                print(f"채팅 내역 로드 완료: {len(chat_history)}개 메시지")
                
                # 이전 채팅 내역을 클라이언트에게 전송
                history_data = {
                    "type": "history",
                    "messages": [
                        {
                            "id": msg.id,
                            "sender_id": msg.sender_id,
                            "content": msg.message,
                            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                            "chatroom_id": msg.chatroom_id
                        } for msg in chat_history
                    ]
                }
                await websocket.send_text(json.dumps(history_data))
                print(f"채팅 내역 전송 완료: 그룹 채팅방 {chatroom_id}")
            except Exception as e:
                print(f"채팅 내역 로드 실패: {str(e)}")
                # 내역 로드 실패 메시지 전송
                await websocket.send_text(json.dumps({
                    "type": "history_error",
                    "message": "채팅 내역을 불러오는 중 오류가 발생했습니다."
                }))
            
            # 메시지 수신 루프
            while True:
                print(f"메시지 수신 대기: 그룹 채팅방 {chatroom_id}")
                data = await websocket.receive_text()
                print(f"메시지 수신됨: 그룹 채팅방 {chatroom_id}")
                
                try:
                    message_data = json.loads(data)
                    
                    # 메시지 타입이 'chat'인 경우 데이터베이스에 저장
                    if message_data.get("type") == "chat" and user_id:
                        try:
                            print(f"메시지 저장 시작: 그룹 채팅방 {chatroom_id}")
                            # 내용 확인을 위한 디버깅 로그
                            print(f"저장할 메시지 내용: {message_data.get('content')}")
                            
                            message_create = GroupChatMessageCreate(
                                chatroom_id=chatroom_id,
                                sender_id=int(user_id),
                                content=message_data.get("content")  # 필드명 일치
                            )
                            
                            saved_message = await create_chat_message(db, message_create)
                            print(f"메시지 저장 성공, ID: {saved_message.id}")
                            
                        except Exception as e:
                            print(f"메시지 저장 실패: {str(e)}")
                            import traceback
                            print(f"상세 오류: {traceback.format_exc()}")
                    
                    # 메시지를 발신자를 제외한 모든 사용자에게 전달
                    print(f"메시지 브로드캐스트 시작: 그룹 채팅방 {chatroom_id}")
                    await group_chat_manager.broadcast(chatroom_id, data, email)
                    print(f"메시지 브로드캐스트 완료: 그룹 채팅방 {chatroom_id}")
                    
                except json.JSONDecodeError:
                    print(f"JSON 파싱 실패: 그룹 채팅방 {chatroom_id}")
                    # 일반 텍스트인 경우 그대로 전달
                    await group_chat_manager.broadcast(chatroom_id, data, email)
                
        except WebSocketDisconnect:
            # 연결 종료 시 매니저에서 제거
            print(f"웹소켓 연결 종료: 그룹 채팅방 {chatroom_id}")
            group_chat_manager.disconnect(chatroom_id, websocket)
            
    except JWTError as e:
        print(f"JWT 오류: 그룹 채팅방 {chatroom_id}, {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "인증 토큰이 유효하지 않습니다."
        }))
        await websocket.close()
    except Exception as e:
        print(f"예상치 못한 오류: 그룹 채팅방 {chatroom_id}, {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"연결 중 오류가 발생했습니다: {str(e)}"
        }))
        await websocket.close()