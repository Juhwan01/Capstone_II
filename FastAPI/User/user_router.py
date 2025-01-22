from fastapi import APIRouter, Depends
from core.database import provide_session
from .user_schema import (TransDTO, TransCloseDTO)
from .user_crud import UserCRUD

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

@router.post("/make_trans")
async def make_transaction(payload:TransDTO,db=Depends(provide_session)):
    crud = UserCRUD(session=db)
    trans = await crud.make_transaction(payload=payload)
    return trans

@router.post("/close_trans")
async def close_transaction(payload:TransCloseDTO,db=Depends(provide_session)):
    crud = UserCRUD(session=db)
    return await crud.close_transaction(trans_id=payload.trans_id)