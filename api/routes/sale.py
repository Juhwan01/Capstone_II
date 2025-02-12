from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db
from schemas.sale import SaleCreate, SaleResponse
from crud.crud_sale import CRUDsale
from utils.form_parser import parse_sale_form  # ✅ Form 데이터 변환 유틸리티 추가

router = APIRouter()

@router.post("/sales/", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate = Depends(parse_sale_form),  # ✅ Form 데이터 자동 변환
    file: UploadFile = File(...),  # ✅ 이미지 파일 업로드 추가
    db: AsyncSession = Depends(get_async_db)
):
    """
    판매 등록 엔드포인트 (AWS S3 이미지 업로드 포함)
    """
    sale_service = CRUDsale(db)
    result = await sale_service.register_sale(sale_data, file)  # ✅ `dict()` 제거하여 직접 전달

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.delete("/sales/{sale_id}")
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    판매 삭제 엔드포인트 (AWS S3 이미지 삭제 포함)
    """
    sale_service = CRUDsale(db)
    result = await sale_service.delete_sale(sale_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": "Sale and image successfully deleted"}
