from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.transaction import (TransDTO)
from models.models import IngredientRequest, Transaction
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_GeomFromEWKT

class CRUDtransaction:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def make_transaction(self, payload: TransDTO):
        transaction_location = f"POINT({payload.transaction_loc[1]} {payload.transaction_loc[0]})"
        new_trans = Transaction(
            seller_id=payload.seller_id,
            buyer_id=payload.buyer_id,
            request_id=payload.request_id,
            transaction_location=ST_GeomFromEWKT(transaction_location)
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

    async def success(self, trans_id: int):
        result = await self._session.execute(select(Transaction).filter_by(id=trans_id))
        transaction = result.scalars().first()
        if transaction:
            re_id = transaction.request_id
            request_result = await self._session.execute(select(IngredientRequest).filter_by(id=re_id))
            request = request_result.scalars().first()
            if request:
                request.status = "Completed"
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