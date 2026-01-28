"""add_client_code_and_employee_code_fields

Revision ID: 3ae4af283411
Revises: 32b395f52e9f
Create Date: 2026-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ae4af283411'
down_revision: Union[str, Sequence[str], None] = '32b395f52e9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add client code and employee code fields."""
    # Add code column to clients table
    op.add_column('clients', sa.Column('code', sa.String(length=5), nullable=True))
    
    # Create index on clients.code for uniqueness checks
    op.create_index('ix_clients_code', 'clients', ['code', 'tenant_id'], unique=False)
    
    # Add family_id column to persons table
    op.add_column('persons', sa.Column('family_id', sa.String(length=25), nullable=True))
    
    # Create foreign key constraint for family_id
    op.create_foreign_key(
        'fk_persons_family_id',
        'persons', 'persons',
        ['family_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index on family_id for queries
    op.create_index('ix_persons_family_id', 'persons', ['family_id'], unique=False)
    
    # Note: employment_info JSON structure will be updated by application code
    # The JSON column itself doesn't need migration, but existing data will need
    # to be migrated to include client_id and employee_code fields


def downgrade() -> None:
    """Remove client code and employee code fields."""
    # Drop index and foreign key
    op.drop_index('ix_persons_family_id', table_name='persons')
    op.drop_constraint('fk_persons_family_id', 'persons', type_='foreignkey')
    
    # Drop columns
    op.drop_column('persons', 'family_id')
    op.drop_index('ix_clients_code', table_name='clients')
    op.drop_column('clients', 'code')
