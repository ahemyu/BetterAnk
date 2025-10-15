"""add_parent_deck_id_to_decks

Revision ID: a953154418af
Revises: 2627407c2584
Create Date: 2025-10-15 19:48:27.954258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a953154418af'
down_revision: Union[str, None] = '2627407c2584'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add parent_deck_id column to decks table
    op.add_column('decks', sa.Column('parent_deck_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_decks_parent_deck_id'), 'decks', ['parent_deck_id'], unique=False)
    op.create_foreign_key('fk_decks_parent_deck_id', 'decks', 'decks', ['parent_deck_id'], ['id'])


def downgrade() -> None:
    # Remove parent_deck_id column from decks table
    op.drop_constraint('fk_decks_parent_deck_id', 'decks', type_='foreignkey')
    op.drop_index(op.f('ix_decks_parent_deck_id'), table_name='decks')
    op.drop_column('decks', 'parent_deck_id')
