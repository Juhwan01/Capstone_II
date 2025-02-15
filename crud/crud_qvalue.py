from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from crud.base import CRUDBase
from models.models import QValue
from schemas import QValueCreate, QValueUpdate

class CRUDQValue(CRUDBase[QValue, QValueCreate, QValueUpdate]):
    async def get_qvalue(
        self, 
        db: AsyncSession, 
        user_id: int, 
        recipe_id: int
    ) -> Optional[QValue]:
        """Q-value 조회"""
        result = await db.execute(
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.recipe_id == recipe_id
            )
        )
        return result.scalar_one_or_none()

    async def update_qvalue(
        self, 
        db: AsyncSession, 
        qvalue: QValue, 
        new_value: float
    ) -> QValue:
        """Q-value 업데이트"""
        qvalue.value = new_value
        db.add(qvalue)
        await db.commit()
        await db.refresh(qvalue)
        return qvalue

qvalue = CRUDQValue(QValue)