from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db
from schemas.sale import SaleCreate, SaleResponse
from crud.crud_sale import CRUDsale
from services.s3_service import upload_images_to_s3
from utils.form_parser import parse_sale_form

router = APIRouter()

@router.post("/sales/", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate = Depends(parse_sale_form),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_async_db)
):
    """
    판매 등록 엔드포인트 (AWS S3 이미지 업로드 포함)
    """
    sale_service = CRUDsale(db)

    # 이미지 파일 확장자 검사만 수행
    for file in files:
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in {'png', 'jpg', 'jpeg', 'gif'}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension: {file_ext}"
            )

    # S3 업로드
    image_urls = await upload_images_to_s3(files)
    if not image_urls:
        raise HTTPException(status_code=500, detail="Failed to upload images to S3")

    # 판매 등록 및 이미지 저장
    result = await sale_service.register_sale(sale_data, image_urls)

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

    return {"message": "Sale and images successfully deleted"}