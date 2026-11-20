
"""initial schema

Revision ID: e7f2a8269922
Revises:
Create Date: 2026-11-19 00:14:35.657540
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f2a8269922'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'monitors',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('interval_seconds', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('TRUE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint('interval_seconds > 0', name='check_interval')
    )

    op.create_table(
        'check_results',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('monitor_id', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['monitor_id'],
            ['monitors.id'],
            name='fk_monitor',
            ondelete='CASCADE'
        ),
        sa.CheckConstraint("status IN ('UP', 'DOWN')", name='check_status'),
        sa.CheckConstraint(
            'response_time_ms IS NULL OR response_time_ms >= 0',
            name='check_response_time'
        )
    )

    op.create_index(
        'idx_check_results_monitor_checked',
        'check_results',
        ['monitor_id', sa.text('checked_at DESC')],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(
        'idx_check_results_monitor_checked',
        table_name='check_results'
    )
    op.drop_table('check_results')
    op.drop_table('monitors')