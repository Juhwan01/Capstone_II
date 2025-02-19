import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.models import Sale, Ingredient, User
from schemas.sale import SaleCreate
from services.s3_service import upload_image_to_s3, delete_image_from_s3
from fastapi import UploadFile
from datetime import datetime
import pytz

class CRUDsale:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_sale(self, sale_data: SaleCreate, file: UploadFile) -> dict:
        """상품을 등록하고 AWS S3에 이미지를 업로드"""
        try:
            # ✅ Ingredient 존재 확인
            ingredient = await self.db.execute(
                select(Ingredient).where(Ingredient.id == sale_data.ingredient_id)
            )
            ingredient = ingredient.scalars().first()
            if not ingredient:
                return {"error": f"Ingredient with ID {sale_data.ingredient_id} does not exist"}

            # ✅ User 존재 확인
            seller = await self.db.execute(
                select(User).where(User.id == sale_data.seller_id)
            )
            seller = seller.scalars().first()
            if not seller:
                return {"error": f"Seller with ID {sale_data.seller_id} does not exist"}

            # ✅ AWS S3 이미지 업로드
            image_url = await upload_image_to_s3(file)
            if not image_url:
                return {"error": "S3 이미지 업로드 실패"}

            # ✅ 날짜 변환 (UTC 변환)
            expiry_date = sale_data.expiry_date
            if isinstance(expiry_date, datetime) and expiry_date.tzinfo:
                expiry_date = expiry_date.astimezone(pytz.UTC).replace(tzinfo=None)

            # ✅ Sale 인스턴스 생성
            sale = Sale(
                ingredient_id=sale_data.ingredient_id,
                ingredient_name=sale_data.ingredient_name,
                seller_id=sale_data.seller_id,
                title = sale_data.title ,
                value=sale_data.value,
                location_lat=sale_data.location_lat,
                location_lon=sale_data.location_lon,
                expiry_date=expiry_date,
                status=sale_data.status,
                contents =sale_data.contents,
                image_url=image_url  # ✅ S3에서 반환된 이미지 URL 저장
            )

            # ✅ 데이터베이스에 추가
            self.db.add(sale)
            await self.db.commit()
            await self.db.refresh(sale)

            return {
                "message": "Sale successfully registered",
                "id": sale.id,
                "ingredient_id": sale.ingredient_id,
                "ingredient_name": sale.ingredient_name,
                "seller_id": sale.seller_id,
                "value": sale.value,
                "title" : sale.title,
                "location": {
                    "latitude": sale.location_lat,
                    "longitude": sale.location_lon,
                },
                "expiry_date": sale.expiry_date,
                "status": sale.status,
                "image_url": sale.image_url,
                "contents" : sale.contents
            }

        except IntegrityError as e:
            await self.db.rollback()
            print(f"🚨 IntegrityError: {e}")
            return {"error": "Database integrity error", "details": str(e)}

        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 Unexpected error: {e}")
            return {"error": "Unexpected error", "details": str(e)}

    async def delete_sale(self, sale_id: int) -> dict:
        """상품 삭제 및 AWS S3 이미지 삭제"""
        try:
            result = await self.db.execute(select(Sale).where(Sale.id == sale_id))
            sale = result.scalar_one_or_none()

            if not sale:
                return {"error": "Sale not found"}

            image_url = sale.image_url  # 삭제할 이미지 URL 저장

            # ✅ DB에서 상품 삭제
            await self.db.delete(sale)
            await self.db.commit()

            # ✅ AWS S3에서 이미지 삭제 (이미지가 있는 경우)
            if image_url:
                success = await delete_image_from_s3(image_url)
                if not success:
                    return {"error": "Failed to delete image from S3"}

            return {"message": "Sale and image successfully deleted"}

        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 Unexpected error during sale deletion: {e}")
            return {"error": "Unexpected error", "details": str(e)}
