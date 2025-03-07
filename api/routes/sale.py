from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from api.dependencies import get_async_db
from schemas.sale import SaleCreate, SaleResponse
from crud.crud_sale import CRUDsale
from services.s3_service import delete_images_from_s3, upload_images_to_s3
from services.sale_serivce import SaleService
from utils.form_parser import parse_sale_form

router = APIRouter()

@router.post("/sales", response_model=SaleResponse)
async def create_sale(
    sale_data: SaleCreate = Depends(parse_sale_form),
    files: Optional[List[UploadFile]] = File(None),
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

@router.put("/sales/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: int,
    sale_data: SaleCreate = Depends(parse_sale_form),
    files: Optional[List[UploadFile]] = File(None),  # 이미지 업데이트 선택적
    db: AsyncSession = Depends(get_async_db)
):
    """
    판매 정보 수정 엔드포인트
    - 제목, 가격, 수량(amount), 내용 등 변경 가능
    - 이미지 변경 시 기존 이미지 삭제 후 새 이미지 업로드
    """
    sale_service = CRUDsale(db)

    # 기존 판매 정보 가져오기
    result = await sale_service.get_sale_by_id(sale_id)
    if not result:
        raise HTTPException(status_code=404, detail="Sale not found")

    # **이미지 변경을 원할 경우**: 기존 이미지 삭제 후 새 이미지 업로드
    image_urls = None  # 기본값은 None (변경하지 않을 경우)
    if files:
        for file in files:
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in {'png', 'jpg', 'jpeg', 'gif'}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file extension: {file_ext}"
                )

        # 기존 이미지 삭제 (S3에서 삭제)
        existing_images = [img.image_url for img in result.images]
        if existing_images:
            await delete_images_from_s3(existing_images)

        # 새로운 이미지 업로드
        image_urls = await upload_images_to_s3(files)
        if not image_urls:
            raise HTTPException(status_code=500, detail="Failed to upload new images to S3")

    # 판매 정보 업데이트 수행
    update_result = await sale_service.update_sale(sale_id, sale_data, image_urls)

    if "error" in update_result:
        raise HTTPException(status_code=400, detail=update_result["error"])

    return update_result


@router.get("/sales", response_model=List[SaleResponse])
async def get_all_sales(db: AsyncSession = Depends(get_async_db)):
    """
    모든 판매 상품 조회 API
    """
    sale_service = CRUDsale(db)
    sales = await sale_service.get_all_sales()

    return sales
@router.get("/sales/location", response_model=List[SaleResponse])
async def get_sales_by_location(
    user_lat: float,
    user_lon: float,
    radius: int = 1000,  # 기본 반경 5km
    db: AsyncSession = Depends(get_async_db)
):
    """
    특정 위치 기준으로 반경 N km 내 판매 상품 조회 API
    """
    sale_service = CRUDsale(db)
    return await sale_service.get_sales_by_location(user_lat, user_lon, radius)