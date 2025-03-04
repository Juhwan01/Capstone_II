from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func, and_
from geoalchemy2.elements import WKTElement
from schemas.transaction import (TransDTO, ArriveDTO)
from models.models import Sale, Transaction, User, Ingredient
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_GeomFromEWKT
from datetime import datetime, timedelta

class CRUDtransaction:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def make_transaction(self, payload: TransDTO):
        new_trans = Transaction(
            buyer_id=payload.buyer_id,
            sale_id=payload.sale_id,
            appointment_time=payload.appointment_time
        )
        result = await self._session.execute(
            select(Sale).filter_by(id=payload.sale_id)
        )
        sale = result.scalars().first()
        if not sale:
            raise ValueError("sale not found.")
        sale.status = "Trading"
        self._session.add(new_trans)
        await self._session.commit()
        return new_trans
    
    async def arrive(self, payload:ArriveDTO):
        trans_result = await self._session.execute(select(Transaction).filter(and_(Transaction.sale_id == payload.sale_id, Transaction.status == "Trading")))
        trans = trans_result.scalars().first()
        if not trans:
            return 1
        location_wkt = f'POINT({payload.location[0]} {payload.location[1]})'
        location = WKTElement(location_wkt, srid=4326)
        result = await self._session.execute(select(Sale).filter_by(id=trans.sale_id))
        sale = result.scalars().first()
        sale_loc_wkt = f'POINT({sale.location_lon} {sale.location_lat})'
        sale_loc = WKTElement(sale_loc_wkt, srid=4326)
        distance_result = await self._session.execute(
            select(func.ST_Distance(
                    func.ST_Transform(location, 3857),
                    func.ST_Transform(sale_loc, 3857)
            ))
        )
        distance = distance_result.scalar()
        print(distance)
        if distance <= 100:
            if sale.seller_id == payload.id:
                trans.seller_time = datetime.now()
                await self._session.commit()
                return True
            elif trans.buyer_id == payload.id:
                trans.buyer_time = datetime.now()
                await self._session.commit()
                return True
            else:
                return False
        else:
            return {"error":"거리가 인증이 되지 않습니다."}
        
    async def success(self, sale_id: int):
        result = await self._session.execute(select(Transaction).filter(and_(Transaction.sale_id == sale_id, Transaction.status == "Trading")))
        transaction = result.scalars().first()
        if transaction and transaction.buyer_time and transaction.seller_time:
            transaction.status = "Complete"
            ap_time = transaction.appointment_time
            by_time = transaction.buyer_time
            sl_time = transaction.seller_time
            sale_id = transaction.sale_id
            sale_result = await self._session.execute(select(Sale).filter_by(id=sale_id))
            sale = sale_result.scalars().first()
            if sale:
                sale.status = "Sold Out"
                buyer_result = await self._session.execute(select(User).filter_by(id=transaction.buyer_id))
                buyer = buyer_result.scalar_one()
                if by_time and by_time <= ap_time:
                    buyer.trust_score += 0.5
                seller_result = await self._session.execute(select(User).filter_by(id=sale.seller_id))
                seller = seller_result.scalar_one()
                if sl_time and sl_time <= ap_time:
                    seller.trust_score += 0.5
                ingred_id = sale.ingredient_id
                ingred = await self._session.execute(select(Ingredient).filter_by(id=ingred_id))
                ingred_data = ingred.scalar_one_or_none()
                print(ingred_data.amount)
                if ingred_data.amount == 0:
                    await self._session.delete(ingred_data)
                    sale.ingredient_id = None
                print(sale.id)
                print(transaction.id)
                print(transaction.sale_id)
                await self._session.commit()
                return 0
        return -1
    
    async def cancel(self, sale_id: int):
        result = await self._session.execute(select(Transaction).filter(and_(Transaction.sale_id == sale_id, Transaction.status == "Trading")))
        transaction = result.scalars().first()
        if transaction:
            transaction.status = "Cancel"
            sale_id = transaction.sale_id
            sale_result = await self._session.execute(select(Sale).filter_by(id=sale_id))
            sale = sale_result.scalars().first()
            if sale:
                sale.status = "Available"
            else:
                return -1
            result_buyer = await self._session.execute(select(User).filter_by(id=transaction.buyer_id))
            buyer = result_buyer.scalar_one_or_none()
            result_seller = await self._session.execute(select(User).filter_by(id=sale_id))
            seller = result_seller.scalar_one_or_none()
            if transaction.appointment_time and (datetime.now() - transaction.appointment_time > timedelta(minutes=10)):
                if  (not transaction.seller_time and not transaction.buyer_time) or (transaction.seller_time and transaction.buyer_time):
                    print(not(transaction.seller_time and transaction.buyer_time))
                    print("seller_time")
                    print(transaction.seller_time)
                    print("buyer_time")
                    print(transaction.buyer_time)
                    return {"is that true?"}
                else:
                    if transaction.seller_time:
                        seller.trust_score -= 15
                        print(seller.trust_score)
                    else:
                        buyer.trust_score -= 15
                        print(buyer.trust_score)
                    await self._session.commit()
            else:
                return{"아직 약속시간 안에 있습니다."}
        else:
            return -1

    async def get_transaction(self, sale_id: int):
        trans_result = await self._session.execute(select(Transaction).filter(and_(Transaction.sale_id == sale_id, Transaction.status == "Trading")))
        return trans_result.scalar_one_or_none()