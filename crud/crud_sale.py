import traceback
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # ✅ 관계 강제 로드 추가
from sqlalchemy.exc import IntegrityError
from models.models import Sale, Ingredient, User, Image
from schemas.sale import SaleCreate
from services.s3_service import upload_images_to_s3, delete_images_from_s3
from fastapi import UploadFile

class CRUDsale:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_sale(self, sale_data: SaleCreate, image_urls: List[str]) -> dict:
        try:
            print(f"📌 저장할 이미지 URL 리스트: {image_urls}")  # ✅ 디버깅 코드 추가

            if not image_urls:
                return {"error": "S3 이미지 업로드 실패"}

            # ✅ Sale 인스턴스 생성
            sale = Sale(
                ingredient_id=sale_data.ingredient_id,
                ingredient_name=sale_data.ingredient_name,
                seller_id=sale_data.seller_id,
                title=sale_data.title,
                value=sale_data.value,
                location_lat=sale_data.location_lat,
                location_lon=sale_data.location_lon,
                expiry_date=sale_data.expiry_date,
                status=sale_data.status,
                contents=sale_data.contents
            )
            self.db.add(sale)
            await self.db.flush()  # ✅ `sale.id`를 얻기 위해 flush 실행

            # ✅ Image 테이블에 `image_urls` 리스트를 저장 (각 URL마다 한 행씩)
            image_objects = [Image(sale_id=sale.id, image_url=url) for url in image_urls]
            self.db.add_all(image_objects)

            # ✅ DB 커밋 및 최신화
            await self.db.commit()

            # ✅ 관계를 최신화하기 위해 `selectinload()` 사용하여 다시 조회
            result = await self.db.execute(
                select(Sale).options(selectinload(Sale.images)).where(Sale.id == sale.id)
            )
            sale = result.scalar_one_or_none()

            # ✅ 디버깅용 로그 출력 (데이터 확인)
            print(f"📌 Sale ID: {sale.id}")
            print(f"📌 Images loaded: {[img.image_url for img in sale.images]}")

            return {
                "message": "Sale successfully registered",
                "id": sale.id,
                "ingredient_id": sale.ingredient_id,
                "ingredient_name": sale.ingredient_name,
                "seller_id": sale.seller_id,
                "title": sale.title,
                "value": sale.value,
                "location": {
                    "latitude": sale.location_lat,
                    "longitude": sale.location_lon,
                },
                "expiry_date": sale.expiry_date,
                "status": sale.status,
                "contents": sale.contents,
                "images" : image_urls  # ✅ images 리스트 반환
            }

        except Exception as e:
            await self.db.rollback()
            print(f"🚨 Unexpected error: {e}")
            traceback.print_exc()
            return {"error": "Unexpected error", "details": str(e)}



    async def delete_sale(self, sale_id: int) -> dict:
        """상품 삭제 및 AWS S3 이미지 삭제"""
        try:
            # ✅ Sale 및 연결된 이미지 조회 (이미지 관계 강제 로드)
            result = await self.db.execute(
                select(Sale).options(selectinload(Sale.images)).where(Sale.id == sale_id)
            )
            sale = result.scalar_one_or_none()

            if not sale:
                return {"error": "Sale not found"}

            # ✅ 연결된 이미지 URL 추출
            image_urls = [img.image_url for img in sale.images] if sale.images else []

            # ✅ DB에서 상품 삭제 (Cascade로 Image도 자동 삭제됨)
            await self.db.delete(sale)
            await self.db.commit()

            # ✅ AWS S3에서 이미지 삭제 (이미지가 있는 경우)
            if image_urls:
                success = await delete_images_from_s3(image_urls)
                if not success:
                    return {"error": "Failed to delete image from S3"}

            return {"message": "Sale and images successfully deleted"}

        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 Unexpected error during sale deletion: {e}")
            return {"error": "Unexpected error", "details": str(e)}
