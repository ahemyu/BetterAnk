"""Placeholder for historical revision 9f958492aa86.

This migration was missing from source control but exists in the target
PostgreSQL database. The upgrade/downgrade hooks are intentionally empty so
that Alembic can recognize the historical revision chain and proceed with
newer migrations.

Revision ID: 9f958492aa86
Revises: 2627407c2584
Create Date: 2025-11-23 09:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9f958492aa86"
down_revision: Union[str, None] = "2627407c2584"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
