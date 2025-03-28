from fastapi import APIRouter, Depends
from api.dependencies import get_async_db, get_current_active_user
from schemas.transaction import (TransDTO, StatusDTO, ArriveDTO)
from crud.crud_transaction import CRUDtransaction

router = APIRouter(
    prefix="/transaction",
    tags=["transaction"],
)

@router.post("/make_trans")
async def make_transaction(payload:TransDTO,db=Depends(get_async_db)):
    crud = CRUDtransaction(session=db)
    trans = await crud.make_transaction(payload=payload)
    return trans

@router.post("/arrive")
async def arrive(payload:ArriveDTO, db=Depends(get_async_db)):
    crud = CRUDtransaction(session=db)
    return await crud.arrive(payload=payload)

@router.post("/success")
async def success(payload:StatusDTO,db=Depends(get_async_db)):
    crud = CRUDtransaction(session=db)
    return await crud.success(sale_id=payload.sale_id)

@router.post("/cancel")
async def cancel(payload:StatusDTO,db=Depends(get_async_db)):
    crud = CRUDtransaction(session=db)
    return await crud.cancel(sale_id=payload.sale_id)

@router.get("/get_trans")
async def get_transaction(sale_id: int, db=Depends(get_async_db)):
    crud = CRUDtransaction(session=db)
    return await crud.get_transaction(sale_id=sale_id)