"""add_client_code_and_employee_code_fields

Revision ID: 3ae4af283411
Revises: 32b395f52e9f
Create Date: 2026-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '3ae4af283411'
down_revision: Union[str, Sequence[str], None] = '32b395f52e9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add client code and employee code fields."""
    connection = op.get_bind()
    inspector = inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('clients')]
    
    if 'code' not in columns:
        op.add_column('clients', sa.Column('code', sa.String(length=5), nullable=True))
    
    result = connection.execute(
        sa.text("SELECT id, tenant_id, name FROM clients WHERE code IS NULL ORDER BY tenant_id, created_at")
    )
    
    tenant_codes = {}
    for row in result:
        client_id, tenant_id, name = row[0], row[1], row[2]
        base_code = ''.join(c.upper() for c in name if c.isalnum())[:5]
        if len(base_code) < 3:
            base_code = client_id[:5].upper()
        
        if tenant_id not in tenant_codes:
            tenant_codes[tenant_id] = set()
        
        code = base_code[:5]
        counter = 1
        while code in tenant_codes[tenant_id]:
            suffix = str(counter)
            code = (base_code[:5-len(suffix)] + suffix)[:5]
            counter += 1
            if counter > 99:
                code = client_id[:5].upper()
                break
        
        tenant_codes[tenant_id].add(code)
        connection.execute(sa.text("UPDATE clients SET code = :code WHERE id = :id"), {"code": code, "id": client_id})
    
    code_column = next((col for col in inspector.get_columns('clients') if col['name'] == 'code'), None)
    if code_column and code_column['nullable']:
        with op.batch_alter_table('clients', schema=None) as batch_op:
            batch_op.alter_column('code', nullable=False)
    
    indexes = [idx['name'] for idx in inspector.get_indexes('clients')]
    if 'ix_clients_code' not in indexes:
        op.create_index('ix_clients_code', 'clients', ['code', 'tenant_id'], unique=False)
    
    persons_columns = [col['name'] for col in inspector.get_columns('persons')]
    if 'family_id' not in persons_columns:
        op.add_column('persons', sa.Column('family_id', sa.String(length=25), nullable=True))
    
    fk_constraints = [fk['name'] for fk in inspector.get_foreign_keys('persons')]
    if 'fk_persons_family_id' not in fk_constraints:
        with op.batch_alter_table('persons', schema=None) as batch_op:
            batch_op.create_foreign_key('fk_persons_family_id', 'persons', ['family_id'], ['id'], ondelete='SET NULL')

    persons_indexes = [idx['name'] for idx in inspector.get_indexes('persons')]
    if 'ix_persons_family_id' not in persons_indexes:
        op.create_index('ix_persons_family_id', 'persons', ['family_id'], unique=False)


def downgrade() -> None:
    """Remove client code and employee code fields."""
    # Drop index
    op.drop_index('ix_persons_family_id', table_name='persons')

    # Drop foreign key and column using batch mode
    with op.batch_alter_table('persons', schema=None) as batch_op:
        batch_op.drop_constraint('fk_persons_family_id', type_='foreignkey')
        batch_op.drop_column('family_id')

    # Drop clients column and index
    op.drop_index('ix_clients_code', table_name='clients')
    op.drop_column('clients', 'code')
