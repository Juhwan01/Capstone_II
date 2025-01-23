from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from schemas.transaction import (TransDTO, TransCloseDTO)
from crud.transaction import TransactionCRUD

router = APIRouter()

@router.post("/make_trans")
async def make_transaction(payload:TransDTO,db=Depends(get_db)):
    crud = TransactionCRUD(session=db)
    trans = await crud.make_transaction(payload=payload)
    return trans

@router.post("/success")
async def success_transaction(payload:TransCloseDTO,db=Depends(get_db)):
    crud = TransactionCRUD(session=db)
    return await crud.close_transaction(trans_id=payload.trans_id)

@router.post("/cancel")
async def cancel_transaction(db=Depends(get_db)):
    return 0