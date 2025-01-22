"""add user role

Revision ID: c288a9fe74be
Revises: 
Create Date: 2025-01-23 00:25:50.762800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c288a9fe74be'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 먼저 enum 타입 생성
    userrole = sa.Enum('CHEF', 'MASTER', 'EXPERT', 'NEWBIE', name='userrole')
    userrole.create(op.get_bind(), checkfirst=True)

    # role 컬럼 추가 (기본값 NEWBIE)
    op.add_column('users',
        sa.Column('role', 
                  sa.Enum('CHEF', 'MASTER', 'EXPERT', 'NEWBIE', name='userrole'),
                  nullable=False,
                  server_default='NEWBIE')
    )
    
    # trust_score 컬럼 추가 (기본값 0.0)
    op.add_column('users',
        sa.Column('trust_score',
                  sa.Float(),
                  nullable=False,
                  server_default='0.0')
    )


def downgrade() -> None:
    # 컬럼 제거
    op.drop_column('users', 'trust_score')
    op.drop_column('users', 'role')
    
    # enum 타입 제거
    op.execute('DROP TYPE userrole')