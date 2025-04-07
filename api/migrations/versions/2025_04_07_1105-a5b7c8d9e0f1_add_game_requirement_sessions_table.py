"""add_game_requirement_sessions_table

Revision ID: a5b7c8d9e0f1
Revises: ee79d9b1c156
Create Date: 2025-04-07 11:05:00.000000

"""
from alembic import op
import models as models
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5b7c8d9e0f1'
down_revision = '9168cc7b9b29'  # 使用正确的前一个版本
branch_labels = None
depends_on = None


def upgrade():
    # 创建game_requirement_sessions表
    op.create_table('game_requirement_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('app_id', sa.String(36), nullable=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(36), nullable=False, server_default='requirements'),
        sa.Column('requirement_data', sa.Text(), nullable=True),
        sa.Column('history_messages', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name='game_requirement_session_pkey')
    )
    
    # 添加索引以提高查询性能
    op.create_index('ix_game_requirement_sessions_app_id', 'game_requirement_sessions', ['app_id'], unique=False)
    op.create_index('ix_game_requirement_sessions_user_id', 'game_requirement_sessions', ['user_id'], unique=False)
    op.create_index('ix_game_requirement_sessions_tenant_id', 'game_requirement_sessions', ['tenant_id'], unique=False)


def downgrade():
    # 移除索引
    op.drop_index('ix_game_requirement_sessions_tenant_id', table_name='game_requirement_sessions')
    op.drop_index('ix_game_requirement_sessions_user_id', table_name='game_requirement_sessions')
    op.drop_index('ix_game_requirement_sessions_app_id', table_name='game_requirement_sessions')
    
    # 删除表
    op.drop_table('game_requirement_sessions')
