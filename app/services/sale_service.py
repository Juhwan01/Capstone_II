import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.sale import Sale
from models.ingredient import Ingredient
from models.user import User
from datetime import datetime

class SaleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_sale(self, sale_data: dict) -> dict:
        try:
            # Ingredient 존재 확인
            ingredient = await self.db.execute(
                select(Ingredient).where(Ingredient.id == sale_data['ingredient_id'])
            )
            ingredient = ingredient.scalars().first()
            if not ingredient:
                return {"error": f"Ingredient with ID {sale_data['ingredient_id']} does not exist"}

            # User 존재 확인
            seller = await self.db.execute(
                select(User).where(User.id == sale_data['seller_id'])
            )
            seller = seller.scalars().first()
            if not seller:
                return {"error": f"Seller with ID {sale_data['seller_id']} does not exist"}

            # Sale 인스턴스 생성
            sale = Sale(
                ingredient_id=sale_data['ingredient_id'],
                ingredient_name = sale_data['ingredient_name'],
                seller_id=sale_data['seller_id'],
                value=sale_data['value'],
                location_lat=sale_data['location_lat'],
                location_lon=sale_data['location_lon'],
                status=sale_data.get('status', 'Available'),  # 기본값 "Available"
            )

            # 데이터베이스에 추가
            self.db.add(sale)
            await self.db.commit()
            await self.db.refresh(sale)

            # 반환 데이터 처리
            return {
                "message": "Sale successfully registered",
                "id": sale.id,
                "ingredient_id": sale.ingredient_id,
                "ingredient_name":sale.ingredient_name,
                "seller_id": sale.seller_id,
                "value": sale.value,
                "location": {
                    "latitude": sale.location_lat,
                    "longitude": sale.location_lon,
                },
                "status": sale.status,
            }
        except IntegrityError as e:
            await self.db.rollback()
            print(f"IntegrityError: {e}")
            return {"error": "Database integrity error", "details": str(e)}
        except Exception as e:
            await self.db.rollback()
            traceback.print_exc()
            print(f"Unexpected error: {e}")
            return {"error": "Unexpected error", "details": str(e)}


