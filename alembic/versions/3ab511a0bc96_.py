"""empty message

Revision ID: 3ab511a0bc96
Revises: 
Create Date: 2025-03-09 20:48:11.713046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3ab511a0bc96'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('transaction', 'sale_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    if op.get_bind().dialect.has_column('user_profiles', 'owned_ingredients'):
        op.drop_column('user_profiles', 'owned_ingredients')


def downgrade() -> None:
    op.add_column('user_profiles', sa.Column('owned_ingredients', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.alter_column('transaction', 'sale_id',
               existing_type=sa.INTEGER(),
               nullable=False)
