"""Initial schema - ACAS Migration

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-09-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create all tables for the ACAS migration
    # This is a clean start - no existing tables assumed
    op.execute('CREATE SCHEMA IF NOT EXISTS acas')
    op.execute('SET search_path TO acas, public')
    
    # We'll create tables in phases matching the business logic services
    op.execute('''
        -- Create basic custom types
        CREATE DOMAIN currency_amount AS NUMERIC(15,4);
        CREATE DOMAIN percentage AS NUMERIC(5,4);
        CREATE DOMAIN exchange_rate AS NUMERIC(10,6);
        CREATE DOMAIN comp3_type AS NUMERIC(15,3);
    ''')
    
    # System configuration tables
    op.create_table('system_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(60), nullable=False),
        sa.Column('address_line1', sa.String(60)),
        sa.Column('address_line2', sa.String(60)),
        sa.Column('address_line3', sa.String(60)),
        sa.Column('postcode', sa.String(10)),
        sa.Column('vat_registration', sa.String(20)),
        sa.Column('company_registration', sa.String(20)),
        sa.Column('base_currency', sa.String(3), default='USD'),
        sa.Column('fiscal_year_start', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(20), nullable=False),
        sa.Column('full_name', sa.String(60)),
        sa.Column('email', sa.String(120)),
        sa.Column('hashed_password', sa.String(128)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('permission_level', sa.Integer(), default=1),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Company periods table
    op.create_table('company_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('year_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('is_open', sa.Boolean(), default=True),
        sa.Column('is_current', sa.Boolean(), default=False),
        sa.Column('gl_closed', sa.Boolean(), default=False),
        sa.Column('sl_closed', sa.Boolean(), default=False),
        sa.Column('pl_closed', sa.Boolean(), default=False),
        sa.Column('stock_closed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('period_number', 'year_number')
    )
    
    print("Phase 1: System tables created successfully")


def downgrade() -> None:
    op.execute('SET search_path TO acas, public')
    op.drop_table('company_periods')
    op.drop_table('users')
    op.drop_table('system_config')
    op.execute('DROP DOMAIN IF EXISTS comp3_type')
    op.execute('DROP DOMAIN IF EXISTS exchange_rate')
    op.execute('DROP DOMAIN IF EXISTS percentage')
    op.execute('DROP DOMAIN IF EXISTS currency_amount')
    op.execute('DROP SCHEMA IF EXISTS acas CASCADE')