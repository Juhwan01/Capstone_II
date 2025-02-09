"""empty message

Revision ID: c78dfed367ec
Revises: 
Create Date: 2025-02-08 23:58:07.056379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c78dfed367ec'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 임시 JSONB 컬럼 생성
    op.add_column('recipes', sa.Column('ingredients_jsonb', postgresql.JSONB(), nullable=True))
    
    # 기존 텍스트 데이터를 JSON으로 파싱하여 새 컬럼에 복사
    op.execute("""
        UPDATE recipes 
        SET ingredients_jsonb = CASE
            WHEN ingredients IS NULL THEN '{}'::jsonb
            WHEN ingredients = '데이터 없음' THEN '{}'::jsonb
            ELSE ingredients::jsonb
        END
        WHERE ingredients IS NOT NULL
    """)
    
    # 기존 컬럼 삭제
    op.drop_column('recipes', 'ingredients')
    
    # 새 컬럼 이름 변경
    op.alter_column('recipes', 'ingredients_jsonb', new_column_name='ingredients')


def downgrade() -> None:
    # JSONB를 TEXT로 되돌리기
    op.alter_column('recipes', 'ingredients',
                    type_=sa.Text(),
                    postgresql_using='ingredients::text',
                    existing_nullable=True)