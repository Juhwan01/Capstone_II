from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db
from schemas.sale import SaleCreate, SaleResponse
from crud.crud_sale import CRUDsale

router = APIRouter()

@router.post("/sales/", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    판매 등록 엔드포인트
    """
    sale_service = CRUDsale(db)
    result = await sale_service.register_sale(sale_data.dict())

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
