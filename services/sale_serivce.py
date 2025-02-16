from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from crud.crud_sale import CRUDsale
from schemas.sale import SaleCreate
from services.s3_service import upload_image_to_s3, delete_image_from_s3

async def process_sale(db: AsyncSession, sale_data: SaleCreate, file: UploadFile):
    image_url = await upload_image_to_s3(file)
    if not image_url:
        return None

    sale_service = CRUDsale(db)
    return await sale_service.register_sale(sale_data.dict(), file)

async def remove_sale(db: AsyncSession, sale_id: int):
    sale_service = CRUDsale(db)
    result = await sale_service.delete_sale(sale_id)

    if "error" in result:
        return False  # 삭제 실패

    image_url = result.get("image_url")
    if image_url:
        await delete_image_from_s3(image_url)

    return True
