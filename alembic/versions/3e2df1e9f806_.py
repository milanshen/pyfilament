"""empty message

Revision ID: 3e2df1e9f806
Revises: 99538300054a
Create Date: 2025-04-17 20:17:24.545278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '3e2df1e9f806'
down_revision: Union[str, None] = '99538300054a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('task_type', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_task_type_func_address', ['func_address'])


def downgrade() -> None:
    with op.batch_alter_table('task_type', schema=None) as batch_op:
        batch_op.drop_constraint('uq_task_type_func_address', type_='unique')