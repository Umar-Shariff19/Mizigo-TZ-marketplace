"""Add image_url to products

Revision ID: 0002_add_product_image_url
Revises: 0001_initial_schema
Create Date: 2026-11-16
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_product_image_url"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "image_url")
