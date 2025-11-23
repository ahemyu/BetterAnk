"""Add parent deck relation

Revision ID: 20251123_add_deck_parent
Revises: 2627407c2584
Create Date: 2025-11-23 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251123_add_deck_parent"
down_revision: Union[str, None] = "9f958492aa86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("decks", sa.Column("parent_id", sa.Integer(), nullable=True))
    op.create_index("ix_decks_parent_id", "decks", ["parent_id"], unique=False)
    op.create_foreign_key(
        "fk_decks_parent_id",
        "decks",
        "decks",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_decks_parent_id", "decks", type_="foreignkey")
    op.drop_index("ix_decks_parent_id", table_name="decks")
    op.drop_column("decks", "parent_id")
