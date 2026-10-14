"""Add embedded_sub_topic column to Exercise table

Revision ID: 08f91de7d24d
Revises: 803007d63b77
Create Date: 2026-10-06 16:49:07.677693

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "08f91de7d24d"
down_revision: str | Sequence[str] | None = "803007d63b77"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("exercises", sa.Column("embedded_sub_topic", Vector(768), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("exercises", "embedded_sub_topic")
