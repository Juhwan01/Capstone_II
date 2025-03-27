from sqlalchemy.orm import Session
from crud.crud_group_chat import get_chatroom

def check_chatroom_exists(db: Session, group_purchase_id: int):
    return get_chatroom(db, group_purchase_id) is not None
