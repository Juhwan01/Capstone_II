import traceback
from typing import List, Optional
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # ✅ 관계 강제 로드 추가
from sqlalchemy.exc import IntegrityError
from models.models import Sale, Ingredient, User, Image
from schemas.sale import SaleCreate, SaleImageResponse, SaleResponse
from services.s3_service import upload_images_to_s3, delete_images_from_s3
from fastapi import UploadFile
from sqlalchemy.orm import joinedload 


class CRUDsale:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def register_sale(self, sale_data: SaleCreate, image_urls: List[str]) -> dict:
        try:
            print(f"📌 저장할 이미지 URL 리스트: {image_urls}")  # ✅ 디버깅 코드 추가

            # ✅ Ingredient 테이블에서 재료 조회
            ingredient_result = await self.db.execute(
                select(Ingredient).where(Ingredient.id == sale_data.ingredient_id)
            )
            ingredient = ingredient_result.scalar_one_or_none()

            if ingredient:
                # ✅ amount가 충분한지 확인 후 차감
                if ingredient.amount >= sale_data.amount:
                    ingredient.amount -= sale_data.amount
                    await self.db.flush()  # 변경사항 반영
                else:
                    return {"error": "재고 부족: 해당 재료의 수량이 부족합니다."}
            else:
                return {"error": "해당 재료를 찾을 수 없습니다."}

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
                contents=sale_data.contents,
                amount=sale_data.amount  # ✅ 추가된 amount 값 저장
            )
            self.db.add(sale)
            await self.db.flush()  # ✅ `sale.id`를 얻기 위해 flush 실행

            # ✅ 이미지가 있을 경우에만 Image 테이블에 저장
            if image_urls:
                image_objects = [Image(sale_id=sale.id, image_url=url) for url in image_urls]
                self.db.add_all(image_objects)

            # ✅ DB 커밋
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
                "amount": sale.amount,  # ✅ 추가된 amount 반환
                "images": image_urls  # ✅ 빈 리스트일 수도 있음
            }

        except Exception as e:
            await self.db.rollback()
            print(f"🚨 Unexpected error: {e}")
            traceback.print_exc()
            return {"error": "Unexpected error", "details": str(e)}


    async def delete_sale(self, sale_id: int) -> dict:
        """상품 삭제 및 AWS S3 이미지 삭제, Ingredient.amount 복구"""
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

            # ✅ 관련된 Ingredient 테이블에서 원래 amount 복구
            ingredient_result = await self.db.execute(
                select(Ingredient).where(Ingredient.id == sale.ingredient_id)
            )
            ingredient = ingredient_result.scalar_one_or_none()

            if ingredient:
                ingredient.amount += sale.amount  # ✅ 판매 취소된 수량만큼 복구
                await self.db.flush()

            # ✅ DB에서 Sale 삭제 (Cascade로 Image도 자동 삭제됨)
            await self.db.delete(sale)
            await self.db.commit()

            # ✅ AWS S3에서 이미지 삭제 (이미지가 있는 경우)
            if image_urls:
                success = await delete_images_from_s3(image_urls)
                if not success:
                    return {"error": "Failed to delete images from S3"}

            return {"message": "Sale and images successfully deleted, Ingredient amount restored"}

        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 Unexpected error during sale deletion: {e}")
            return {"error": "Unexpected error", "details": str(e)}

    async def update_sale(self, sale_id: int, sale_data: SaleCreate, image_urls: Optional[List[str]]) -> dict:
        """판매 정보 수정 및 Ingredient.amount 조정 (이미지 변경 반영)"""
        try:
            # ✅ 기존 Sale 데이터 조회
            result = await self.db.execute(
                select(Sale).options(selectinload(Sale.images)).where(Sale.id == sale_id)
            )
            sale = result.scalar_one_or_none()

            if not sale:
                return {"error": "Sale not found"}

            previous_amount = sale.amount  # 기존 amount 저장

            # ✅ 관련된 Ingredient 데이터 조회
            ingredient_result = await self.db.execute(
                select(Ingredient).where(Ingredient.id == sale.ingredient_id)
            )
            ingredient = ingredient_result.scalar_one_or_none()

            # ✅ amount 값이 변경된 경우 Ingredient 테이블 수정
            if ingredient:
                amount_difference = sale_data.amount - previous_amount
                if ingredient.amount >= -amount_difference:  # ✅ 재고 부족 방지
                    ingredient.amount -= amount_difference
                    await self.db.flush()
                else:
                    return {"error": "재고 부족: 수정할 수 없습니다."}

            # ✅ Sale 정보 업데이트
            sale.ingredient_id = sale_data.ingredient_id
            sale.ingredient_name = sale_data.ingredient_name
            sale.seller_id = sale_data.seller_id
            sale.title = sale_data.title
            sale.value = sale_data.value
            sale.location_lat = sale_data.location_lat
            sale.location_lon = sale_data.location_lon
            sale.expiry_date = sale_data.expiry_date
            sale.status = sale_data.status
            sale.contents = sale_data.contents
            sale.amount = sale_data.amount  # ✅ 수정된 amount 반영

            # ✅ 이미지 변경이 있는 경우: 기존 이미지 삭제 후 새 이미지 추가
            if image_urls is not None:
                # 기존 이미지 삭제
                await self.db.execute(
                    delete(Image).where(Image.sale_id == sale_id)
                )
                await self.db.flush()

                # 새 이미지 추가
                new_image_objects = [Image(sale_id=sale.id, image_url=url) for url in image_urls]
                self.db.add_all(new_image_objects)

            await self.db.commit()

            return {
                "message": "Sale successfully updated",
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
                "amount": sale.amount,
                "images": image_urls if image_urls else [img.image_url for img in sale.images]  # ✅ 이미지 반영
            }

        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"🚨 Unexpected error during sale update: {e}")
            return {"error": "Unexpected error", "details": str(e)}

    async def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """
        특정 Sale 정보를 조회 (이미지 포함)
        """
        result = await self.db.execute(
            select(Sale).options(selectinload(Sale.images)).where(Sale.id == sale_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_sales(self):
            """ 등록된 모든 상품 조회 (이미지 포함) """
            result = await self.db.execute(
                select(Sale).options(selectinload(Sale.images))
            )
            sales = result.scalars().all()

            # ✅ SaleResponse 형식으로 변환
            sales_list = []
            for sale in sales:
                    sales_list.append(SaleResponse(
                    id=sale.id,
                    ingredient_id=sale.ingredient_id,
                    ingredient_name=sale.ingredient_name,
                    seller_id=sale.seller_id,
                    title=sale.title,
                    value=sale.value,
                    location={  # ✅ location 필드 추가
                    "latitude": sale.location_lat,
                    "longitude": sale.location_lon
                    },
                    expirate=sale.expiry_date,
                    status=sale.status,
                    amount=sale.amount,
                    contents=sale.contents,
                    images=[SaleImageResponse(image_url=img.image_url) for img in sale.images]
                ))
            return sales_list
    from sqlalchemy.orm import joinedload

    async def get_sales_by_location(self, user_lat: float, user_lon: float, radius: int = 5000):
            """
            특정 위치를 기준으로 반경 N km 내의 상품을 조회하는 메서드
            - `earth_distance`를 활용하여 반경 N km 내의 상품을 필터링
            - `joinedload(Sale.images)`를 사용하여 이미지까지 로드
            """
            query = (
                select(Sale)
                .options(joinedload(Sale.images))  # ✅ 이미지 데이터 로드 추가
                .where(
                    text("""
                        earth_distance(
                            ll_to_earth(CAST(:user_lat AS DOUBLE PRECISION), CAST(:user_lon AS DOUBLE PRECISION)),
                            ll_to_earth(location_lat, location_lon)
                        ) <= CAST(:radius AS DOUBLE PRECISION)
                    """)
                )
            )
            result = await self.db.execute(query, {
                "user_lat": user_lat,
                "user_lon": user_lon,
                "radius": radius
            })

            sales = result.unique().scalars().all()  # ✅ 중복 데이터 제거 추가

            # 🚀 SaleResponse 객체 리스트로 변환
            return [
                SaleResponse(
                    id=sale.id,
                    ingredient_id=sale.ingredient_id,
                    ingredient_name=sale.ingredient_name,
                    seller_id=sale.seller_id,
                    title=sale.title,
                    value=sale.value,
                    location={"latitude": sale.location_lat, "longitude": sale.location_lon},
                    expiry_date=sale.expiry_date,
                    status=sale.status,
                    amount=sale.amount,
                    contents=sale.contents,
                    images=[img.image_url for img in sale.images]  # ✅ 이미지 URL 리스트 반환
                )
                for sale in sales
            ]
