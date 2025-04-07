"""empty message

Revision ID: 424a42812448
Revises: d20049ed0af6, a5b7c8d9e0f1
Create Date: 2025-04-07 09:27:28.113814

"""
from alembic import op
import models as models
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '424a42812448'
down_revision = 'd20049ed0af6'  # 移除对a5b7c8d9e0f1的依赖
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
