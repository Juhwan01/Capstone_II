from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.transaction import (TransDTO, TransCloseDTO)
from models.models import User, IngredientRequest, Transaction

class TransactionCRUD:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def make_transaction(self, payload: TransDTO):
        new_trans = Transaction(
            seller_id=payload.seller_id,
            buyer_id=payload.buyer_id,
            request_id=payload.request_id,
            transaction_location=payload.transaction_loc
        )
        result = await self._session.execute(
            select(IngredientRequest).filter_by(id=payload.request_id)
        )
        request = result.scalars().first()
        if not request:
            raise ValueError("Request not found.")
        request.status = "거래 중"
        self._session.add(new_trans)
        await self._session.commit()
        return new_trans

    async def close_transaction(self, trans_id: int):
        result = await self._session.execute(select(Transaction).filter_by(id=trans_id))
        transaction = result.scalars().first()
        if transaction:
            re_id = transaction.request_id
            request_result = await self._session.execute(select(IngredientRequest).filter_by(id=re_id))
            request = request_result.scalars().first()
            if request:
                request.status = "거래 완료"
                await self._session.commit()
                return 0
        return -1