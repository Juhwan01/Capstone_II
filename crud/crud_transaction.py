from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from geoalchemy2.elements import WKTElement
from schemas.transaction import (TransDTO, ArriveDTO)
from models.models import IngredientRequest, Transaction, User
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_GeomFromEWKT
from datetime import datetime

class CRUDtransaction:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def make_transaction(self, payload: TransDTO):
        transaction_location = f"POINT({payload.transaction_loc[0]} {payload.transaction_loc[1]})"
        new_trans = Transaction(
            seller_id=payload.seller_id,
            buyer_id=payload.buyer_id,
            request_id=payload.request_id,
            transaction_location=transaction_location,
            appointment_time=payload.appointment_time
        )
        result = await self._session.execute(
            select(IngredientRequest).filter_by(id=payload.request_id)
        )
        request = result.scalars().first()
        if not request:
            raise ValueError("Request not found.")
        request.status = "Trading"
        self._session.add(new_trans)
        await self._session.commit()
        return new_trans
    
    async def arrive(self, payload:ArriveDTO):
        trans_result = await self._session.execute(select(Transaction).filter_by(id=payload.trans_id))
        trans = trans_result.scalars().first()
        if not trans:
            return 1
        location_wkt = f'POINT({payload.location[0]} {payload.location[1]})'
        location = WKTElement(location_wkt, srid=4326)
        distance_result = await self._session.execute(
            select(func.ST_Distance(
                    func.ST_Transform(location, 3857),
                    func.ST_Transform(trans.transaction_location, 3857)
            ))
        )
        distance = distance_result.scalar()
        print(distance)
        if distance <= 10:
            if trans.seller_id == payload.id:
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
        
    async def success(self, trans_id: int):
        result = await self._session.execute(select(Transaction).filter_by(id=trans_id))
        transaction = result.scalars().first()
        
        if transaction and transaction.buyer_time and transaction.seller_time:
            ap_time = transaction.appointment_time
            by_time = transaction.buyer_time
            sl_time = transaction.seller_time
            re_id = transaction.request_id
            request_result = await self._session.execute(select(IngredientRequest).filter_by(id=re_id))
            request = request_result.scalars().first()
            if request:
                request.status = "Completed"
                buyer_result = await self._session.execute(select(User).filter_by(id=transaction.buyer_id))
                buyer = buyer_result.scalar_one()
                if by_time and by_time <= ap_time:
                    buyer.trust_score += 0.5
                seller_result = await self._session.execute(select(User).filter_by(id=transaction.seller_id))
                seller = seller_result.scalar_one()
                if sl_time and sl_time <= ap_time:
                    seller.trust_score += 0.5
                await self._session.commit()
                return 0
        return -1
    
    async def cancel(self, trans_id: int):
        result = await self._session.execute(select(Transaction).filter_by(id=trans_id))
        transaction = result.scalars().first()
        if transaction:
            re_id = transaction.request_id
            request_result = await self._session.execute(select(IngredientRequest).filter_by(id=re_id))
            request = request_result.scalars().first()
            if request:
                request.status = "Pending"
                await self._session.commit()
                return 0
        return -1