"""add_party_model_and_party_id_references

Revision ID: 5445c66c9faa
Revises: dc98966dc03b
Create Date: 2025-07-26 01:36:34.243798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5445c66c9faa'
down_revision: Union[str, Sequence[str], None] = 'dc98966dc03b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if parties table exists first
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'parties' not in existing_tables:
        # Create parties table
        op.create_table('parties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('short_name', sa.String(length=50), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('party_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('headquarters', sa.String(length=200), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('social_media_accounts', sa.JSON(), nullable=True),
        sa.Column('scraping_config', sa.JSON(), nullable=True),
        sa.Column('analytics_config', sa.JSON(), nullable=True),
        sa.Column('branding_config', sa.JSON(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )
        
        # Create a default party for existing data
        op.execute("""
            INSERT INTO parties (name, short_name, country, party_type, description, active, created_at, updated_at)
            VALUES ('Reform UK', 'Reform UK', 'United Kingdom', 'political_party', 
                    'Reform UK is a right-wing populist political party in the United Kingdom', 
                    1, datetime('now'), datetime('now'))
        """)
    
    # Check if party_id columns already exist and add them if not
    sources_columns = [col['name'] for col in inspector.get_columns('sources')]
    candidates_columns = [col['name'] for col in inspector.get_columns('candidates')]
    messages_columns = [col['name'] for col in inspector.get_columns('messages')]
    
    if 'party_id' not in sources_columns:
        op.add_column('sources', sa.Column('party_id', sa.Integer(), nullable=False, server_default='1'))
    if 'party_id' not in candidates_columns:
        op.add_column('candidates', sa.Column('party_id', sa.Integer(), nullable=False, server_default='1'))  
    if 'party_id' not in messages_columns:
        op.add_column('messages', sa.Column('party_id', sa.Integer(), nullable=False, server_default='1'))
    
    # Note: SQLite doesn't support adding foreign key constraints after table creation
    # Foreign key relationships are defined in the model but not enforced at DB level for SQLite
    
    # Create indexes if they don't exist
    existing_indexes = [idx['name'] for idx in inspector.get_indexes('messages')]
    if 'idx_messages_party_id' not in existing_indexes:
        op.create_index('idx_messages_party_id', 'messages', ['party_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes
    op.drop_index('idx_messages_party_id', table_name='messages')
    
    # Note: No foreign key constraints to remove (SQLite limitation)
    
    # Drop party_id columns
    op.drop_column('messages', 'party_id')
    op.drop_column('candidates', 'party_id')
    op.drop_column('sources', 'party_id')
    
    # Drop parties table
    op.drop_table('parties')
