"""Create Chapters and Exercises tables

Revision ID: 803007d63b77
Revises: 
Create Date: 2026-10-02 19:27:50.608688

"""
from typing import Sequence, Union
from pgvector.sqlalchemy import Vector


from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '803007d63b77'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table('chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table('exercises',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('sub_topic', sa.Text(), nullable=True),
        sa.Column('task_type', sa.Text(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('rule', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('embedded_summary', Vector(768), nullable=False),
        sa.Column('needs_review', sa.Boolean(), nullable=False),
        sa.Column('review_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('exercises')
    op.drop_table('chapters')
