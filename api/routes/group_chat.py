from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db
from models.models import GroupChatroom, GroupChatMessage
from crud.crud_group_chat import create_chat_message, get_chatroom
from schemas.group_chat import GroupChatMessageCreate

router = APIRouter(prefix="/group-purchases", tags=["group-purchases"])

class GroupChatManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, chatroom_id: int, websocket: WebSocket):
        await websocket.accept()
        if chatroom_id not in self.active_connections:
            self.active_connections[chatroom_id] = []
        self.active_connections[chatroom_id].append(websocket)

    def disconnect(self, chatroom_id: int, websocket: WebSocket):
        self.active_connections[chatroom_id].remove(websocket)
        if not self.active_connections[chatroom_id]:
            del self.active_connections[chatroom_id]

    async def broadcast(self, chatroom_id: int, message: str):
        if chatroom_id in self.active_connections:
            for connection in self.active_connections[chatroom_id]:
                await connection.send_text(message)

chat_manager = GroupChatManager()

@router.websocket("/ws/groupchat/{chatroom_id}/{user_id}")
async def group_chat(websocket: WebSocket, chatroom_id: int, user_id: int, db: AsyncSession = Depends(get_async_db)):
    # ✅ 비동기 방식으로 채팅방 조회
    chatroom = await get_chatroom(db, chatroom_id)
    if not chatroom:
        await websocket.close()
        return

    await chat_manager.connect(chatroom_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()

            # ✅ 비동기 방식으로 메시지 저장
            chat_message = GroupChatMessageCreate(chatroom_id=chatroom_id, sender_id=user_id, message=message)
            await create_chat_message(db, chat_message)  # 비동기 함수로 변경 필요

            # ✅ 메시지 브로드캐스트
            await chat_manager.broadcast(chatroom_id, f"{user_id}: {message}")

    except WebSocketDisconnect:
        chat_manager.disconnect(chatroom_id, websocket)
