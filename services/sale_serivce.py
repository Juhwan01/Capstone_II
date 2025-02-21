from typing import List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from crud.crud_sale import CRUDsale
from schemas.sale import SaleCreate, SaleImageResponse, SaleResponse
from services.s3_service import upload_images_to_s3, delete_images_from_s3

class SaleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sale_crud = CRUDsale(db)

async def process_sale(db: AsyncSession, sale_data: SaleCreate, files: List[UploadFile]):
    image_urls = await upload_images_to_s3(files)  # ✅ S3 업로드 후 URL 리스트 반환
    if not image_urls:
        return None

    print(f"📌 S3 업로드된 이미지 URL 리스트: {image_urls}")  # ✅ 업로드 확인

    sale_service = CRUDsale(db)

    # ✅ `register_sale()`에는 `image_urls` 리스트를 넘김
    return await sale_service.register_sale(sale_data.dict(), image_urls)


async def remove_sale(db: AsyncSession, sale_id: int):
    sale_service = CRUDsale(db)
    result = await sale_service.delete_sale(sale_id)

    if "error" in result:
        return False  # 삭제 실패

    image_url = result.get("image_url")
    if image_url:
        await delete_images_from_s3(image_url)

    return True
