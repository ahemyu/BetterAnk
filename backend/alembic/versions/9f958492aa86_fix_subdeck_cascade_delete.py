"""fix_subdeck_cascade_delete

Revision ID: 9f958492aa86
Revises: a953154418af
Create Date: 2025-10-15 20:32:20.694110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f958492aa86'
down_revision: Union[str, None] = 'a953154418af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing foreign key constraint
    op.drop_constraint('fk_decks_parent_deck_id', 'decks', type_='foreignkey')

    # Recreate the foreign key constraint with CASCADE on delete
    op.create_foreign_key(
        'fk_decks_parent_deck_id',
        'decks',
        'decks',
        ['parent_deck_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop the CASCADE constraint
    op.drop_constraint('fk_decks_parent_deck_id', 'decks', type_='foreignkey')

    # Recreate the foreign key constraint without CASCADE
    op.create_foreign_key(
        'fk_decks_parent_deck_id',
        'decks',
        'decks',
        ['parent_deck_id'],
        ['id']
    )
