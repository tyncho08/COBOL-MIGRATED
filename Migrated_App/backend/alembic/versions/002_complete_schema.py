"""Complete schema migration - All ACAS tables

Revision ID: 002_complete_schema
Revises: 001_initial_schema
Create Date: 2025-09-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_complete_schema'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all remaining ACAS tables"""
    
    # Set search path
    op.execute('SET search_path TO acas, public')
    
    # Create ENUM types (if they don't exist)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'account_type_enum') THEN
                CREATE TYPE account_type_enum AS ENUM ('ASSET', 'LIABILITY', 'CAPITAL', 'INCOME', 'EXPENSE', 'CONTROL', 'MEMO');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'journal_type_enum') THEN
                CREATE TYPE journal_type_enum AS ENUM ('MANUAL', 'SALES', 'PURCHASE', 'CASH_RECEIPT', 'CASH_PAYMENT', 'STOCK', 'PAYROLL', 'OPENING', 'CLOSING', 'ADJUSTMENT', 'REVERSAL');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'posting_status_enum') THEN
                CREATE TYPE posting_status_enum AS ENUM ('DRAFT', 'POSTED', 'REVERSED');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'transaction_status_enum') THEN
                CREATE TYPE transaction_status_enum AS ENUM ('DRAFT', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'INVOICED');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invoice_type_enum') THEN
                CREATE TYPE invoice_type_enum AS ENUM ('STANDARD', 'CREDIT_NOTE', 'DEBIT_NOTE', 'PRO_FORMA');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'purchase_order_status_enum') THEN
                CREATE TYPE purchase_order_status_enum AS ENUM ('DRAFT', 'APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED', 'INVOICED', 'CLOSED', 'CANCELLED');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'goods_receipt_status_enum') THEN
                CREATE TYPE goods_receipt_status_enum AS ENUM ('PENDING', 'PARTIAL', 'RECEIVED', 'CANCELLED');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'irs_transaction_type_enum') THEN
                CREATE TYPE irs_transaction_type_enum AS ENUM ('INCOME', 'EXPENSE', 'ASSET', 'LIABILITY', 'ADJUSTMENT');
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'irs_posting_status_enum') THEN
                CREATE TYPE irs_posting_status_enum AS ENUM ('DRAFT', 'POSTED', 'ADJUSTED');
            END IF;
        END $$;
    """)
    
    print("Phase 1: Creating General Ledger tables...")
    
    # Chart of Accounts
    op.create_table('chart_of_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_code', sa.String(8), nullable=False),
        sa.Column('account_name', sa.String(60), nullable=False),
        sa.Column('account_type', sa.Enum('ASSET', 'LIABILITY', 'CAPITAL', 'INCOME', 'EXPENSE', 'CONTROL', 'MEMO', name='account_type_enum'), nullable=False),
        sa.Column('parent_account', sa.String(8)),
        sa.Column('is_header', sa.Boolean(), default=False),
        sa.Column('level', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_control', sa.Boolean(), default=False),
        sa.Column('control_type', sa.String(20)),
        sa.Column('allow_posting', sa.Boolean(), default=True),
        sa.Column('budget_enabled', sa.Boolean(), default=False),
        sa.Column('analysis_code1_required', sa.Boolean(), default=False),
        sa.Column('analysis_code2_required', sa.Boolean(), default=False),
        sa.Column('analysis_code3_required', sa.Boolean(), default=False),
        sa.Column('currency_code', sa.String(3), default='USD'),
        sa.Column('multi_currency', sa.Boolean(), default=False),
        sa.Column('default_vat_code', sa.String(1)),
        sa.Column('opening_balance', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('current_balance', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('ytd_movement', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_code')
    )
    op.create_index('idx_gl_account_type', 'chart_of_accounts', ['account_type'])
    op.create_index('idx_gl_parent', 'chart_of_accounts', ['parent_account'])
    
    # GL Batches
    op.create_table('gl_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.String(20), nullable=False),
        sa.Column('batch_date', sa.DateTime(), nullable=False),
        sa.Column('batch_type', sa.String(20), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('source_module', sa.String(10)),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('control_count', sa.Integer(), default=0),
        sa.Column('control_debits', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('control_credits', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('actual_count', sa.Integer(), default=0),
        sa.Column('actual_debits', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('actual_credits', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('is_balanced', sa.Boolean(), default=False),
        sa.Column('is_posted', sa.Boolean(), default=False),
        sa.Column('posted_date', sa.DateTime()),
        sa.Column('posted_by', sa.String(20)),
        sa.Column('validation_errors', sa.String(1000)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_number'),
        sa.ForeignKeyConstraint(['period_id'], ['company_periods.id'])
    )
    
    # Journal Headers
    op.create_table('journal_headers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('journal_number', sa.String(20), nullable=False),
        sa.Column('journal_date', sa.DateTime(), nullable=False),
        sa.Column('journal_type', sa.Enum('MANUAL', 'SALES', 'PURCHASE', 'CASH_RECEIPT', 'CASH_PAYMENT', 'STOCK', 'PAYROLL', 'OPENING', 'CLOSING', 'ADJUSTMENT', 'REVERSAL', name='journal_type_enum'), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('period_number', sa.Integer(), nullable=False),
        sa.Column('year_number', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(200), nullable=False),
        sa.Column('reference', sa.String(30)),
        sa.Column('source_module', sa.String(10)),
        sa.Column('source_reference', sa.String(30)),
        sa.Column('posting_status', sa.Enum('DRAFT', 'POSTED', 'REVERSED', name='posting_status_enum'), default='DRAFT'),
        sa.Column('posted_date', sa.DateTime()),
        sa.Column('posted_by', sa.String(20)),
        sa.Column('is_reversal', sa.Boolean(), default=False),
        sa.Column('reversal_of_id', sa.Integer()),
        sa.Column('auto_reverse', sa.Boolean(), default=False),
        sa.Column('reverse_date', sa.DateTime()),
        sa.Column('total_debits', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('total_credits', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('line_count', sa.Integer(), default=0),
        sa.Column('batch_id', sa.Integer()),
        sa.Column('approval_required', sa.Boolean(), default=False),
        sa.Column('approved_by', sa.String(20)),
        sa.Column('approved_date', sa.DateTime()),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('journal_number'),
        sa.ForeignKeyConstraint(['period_id'], ['company_periods.id']),
        sa.ForeignKeyConstraint(['batch_id'], ['gl_batches.id']),
        sa.ForeignKeyConstraint(['reversal_of_id'], ['journal_headers.id'])
    )
    
    # Journal Lines
    op.create_table('journal_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('journal_id', sa.Integer(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('account_code', sa.String(8), nullable=False),
        sa.Column('debit_amount', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('credit_amount', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('currency_code', sa.String(3), default='USD'),
        sa.Column('exchange_rate', postgresql.NUMERIC(10, 6), default=1.0000),
        sa.Column('foreign_debit', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('foreign_credit', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('description', sa.String(200)),
        sa.Column('reference', sa.String(30)),
        sa.Column('analysis_code1', sa.String(10)),
        sa.Column('analysis_code2', sa.String(10)),
        sa.Column('analysis_code3', sa.String(10)),
        sa.Column('quantity', postgresql.NUMERIC(15, 3)),
        sa.Column('unit_description', sa.String(20)),
        sa.Column('vat_code', sa.String(1)),
        sa.Column('vat_amount', postgresql.NUMERIC(15, 4)),
        sa.Column('reconciled', sa.Boolean(), default=False),
        sa.Column('reconciliation_date', sa.DateTime()),
        sa.Column('reconciliation_ref', sa.String(20)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['journal_id'], ['journal_headers.id']),
        sa.ForeignKeyConstraint(['account_id'], ['chart_of_accounts.id']),
        sa.UniqueConstraint('journal_id', 'line_number', name='uq_journal_line')
    )
    op.create_index('idx_journal_line', 'journal_lines', ['journal_id', 'line_number'])
    op.create_index('idx_journal_account', 'journal_lines', ['account_code', 'journal_id'])
    
    print("Phase 2: Creating Customer and Supplier tables...")
    
    # Customers
    op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_code', sa.String(8), nullable=False),
        sa.Column('customer_name', sa.String(60), nullable=False),
        sa.Column('abbreviated_name', sa.String(20)),
        sa.Column('address_line1', sa.String(60)),
        sa.Column('address_line2', sa.String(60)),
        sa.Column('address_line3', sa.String(60)),
        sa.Column('postcode', sa.String(10)),
        sa.Column('country', sa.String(30), default='USA'),
        sa.Column('phone_number', sa.String(20)),
        sa.Column('fax_number', sa.String(20)),
        sa.Column('email_address', sa.String(120)),
        sa.Column('website', sa.String(120)),
        sa.Column('vat_registration', sa.String(20)),
        sa.Column('tax_reference', sa.String(20)),
        sa.Column('credit_limit', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('credit_rating', sa.String(2)),
        sa.Column('payment_terms', sa.Integer(), default=30),
        sa.Column('discount_percentage', postgresql.NUMERIC(5, 4), default=0.0000),
        sa.Column('price_list_code', sa.String(2), default='1'),
        sa.Column('sales_rep_code', sa.String(4)),
        sa.Column('analysis_code1', sa.String(10)),
        sa.Column('analysis_code2', sa.String(10)),
        sa.Column('currency_code', sa.String(3), default='USD'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_on_hold', sa.Boolean(), default=False),
        sa.Column('hold_reason', sa.String(100)),
        sa.Column('date_opened', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('last_sale_date', sa.DateTime()),
        sa.Column('last_payment_date', sa.DateTime()),
        sa.Column('current_balance', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_30', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_60', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_90', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_120', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_code')
    )
    op.create_index('idx_customer_name', 'customers', ['customer_name'])
    
    # Suppliers
    op.create_table('suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(8), nullable=False),
        sa.Column('supplier_name', sa.String(60), nullable=False),
        sa.Column('abbreviated_name', sa.String(20)),
        sa.Column('address_line1', sa.String(60)),
        sa.Column('address_line2', sa.String(60)),
        sa.Column('address_line3', sa.String(60)),
        sa.Column('postcode', sa.String(10)),
        sa.Column('country', sa.String(30), default='USA'),
        sa.Column('phone_number', sa.String(20)),
        sa.Column('fax_number', sa.String(20)),
        sa.Column('email_address', sa.String(120)),
        sa.Column('website', sa.String(120)),
        sa.Column('vat_registration', sa.String(20)),
        sa.Column('tax_reference', sa.String(20)),
        sa.Column('payment_terms', sa.Integer(), default=30),
        sa.Column('discount_percentage', postgresql.NUMERIC(5, 4), default=0.0000),
        sa.Column('currency_code', sa.String(3), default='USD'),
        sa.Column('buyer_code', sa.String(4)),
        sa.Column('analysis_code1', sa.String(10)),
        sa.Column('analysis_code2', sa.String(10)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_on_hold', sa.Boolean(), default=False),
        sa.Column('hold_reason', sa.String(100)),
        sa.Column('date_opened', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('last_purchase_date', sa.DateTime()),
        sa.Column('last_payment_date', sa.DateTime()),
        sa.Column('current_balance', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_30', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_60', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_90', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('aged_120', postgresql.NUMERIC(15, 4), default=0.00),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supplier_code')
    )
    op.create_index('idx_supplier_name', 'suppliers', ['supplier_name'])
    
    print("Phase 3: Creating Stock tables...")
    
    # Stock Items
    op.create_table('stock_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_code', sa.String(15), nullable=False),
        sa.Column('abbreviated_code', sa.String(8)),
        sa.Column('description', sa.String(60), nullable=False),
        sa.Column('extended_description', sa.String(200)),
        sa.Column('unit_of_measure', sa.String(6), default='EACH'),
        sa.Column('alternative_uom', sa.String(6)),
        sa.Column('uom_conversion_factor', postgresql.NUMERIC(10, 6), default=1.000000),
        sa.Column('category_code', sa.String(10)),
        sa.Column('location_code', sa.String(10)),
        sa.Column('bin_location', sa.String(10)),
        sa.Column('is_stocked', sa.Boolean(), default=True),
        sa.Column('is_purchased', sa.Boolean(), default=True),
        sa.Column('is_sold', sa.Boolean(), default=True),
        sa.Column('is_manufactured', sa.Boolean(), default=False),
        sa.Column('is_serialized', sa.Boolean(), default=False),
        sa.Column('quantity_on_hand', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('quantity_allocated', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('quantity_on_order', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('quantity_reserved', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('reorder_level', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('reorder_quantity', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('maximum_level', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('lead_time_days', sa.Integer(), default=7),
        sa.Column('cost_method', sa.String(8), default='AVERAGE'),
        sa.Column('standard_cost', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('average_cost', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('last_cost', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('selling_price1', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('selling_price2', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('selling_price3', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('vat_code', sa.String(1), default='S'),
        sa.Column('weight', postgresql.NUMERIC(10, 3)),
        sa.Column('volume', postgresql.NUMERIC(10, 3)),
        sa.Column('preferred_supplier', sa.String(8)),
        sa.Column('supplier_part_number', sa.String(30)),
        sa.Column('barcode', sa.String(30)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('obsolete_date', sa.DateTime()),
        sa.Column('replacement_item', sa.String(15)),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_code')
    )
    op.create_index('idx_stock_description', 'stock_items', ['description'])
    op.create_index('idx_stock_category', 'stock_items', ['category_code'])
    
    print("Phase 4: Creating Sales Transaction tables...")
    
    # Sales Orders
    op.create_table('sales_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(12), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('customer_code', sa.String(8), nullable=False),
        sa.Column('order_date', sa.DateTime(), nullable=False),
        sa.Column('delivery_date', sa.DateTime()),
        sa.Column('reference', sa.String(30)),
        sa.Column('customer_order_no', sa.String(30)),
        sa.Column('sales_rep', sa.String(20)),
        sa.Column('delivery_address', sa.String(300)),
        sa.Column('payment_terms', sa.String(20)),
        sa.Column('currency_code', sa.String(3), default='USD'),
        sa.Column('exchange_rate', postgresql.NUMERIC(10, 6), default=1.000000),
        sa.Column('status', sa.Enum('DRAFT', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'INVOICED', name='transaction_status_enum'), default='DRAFT'),
        sa.Column('sub_total', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('discount_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('vat_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('total_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('deposit_required', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('deposit_received', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('confirmed_date', sa.DateTime()),
        sa.Column('shipped_date', sa.DateTime()),
        sa.Column('delivered_date', sa.DateTime()),
        sa.Column('tracking_number', sa.String(50)),
        sa.Column('carrier', sa.String(30)),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'])
    )
    op.create_index('idx_sales_order_customer', 'sales_orders', ['customer_id'])
    op.create_index('idx_sales_order_date', 'sales_orders', ['order_date'])
    
    # Sales Order Lines
    op.create_table('sales_order_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('stock_code', sa.String(15), nullable=False),
        sa.Column('description', sa.String(60), nullable=False),
        sa.Column('quantity', postgresql.NUMERIC(15, 3), nullable=False),
        sa.Column('unit_price', postgresql.NUMERIC(15, 4), nullable=False),
        sa.Column('discount_percent', postgresql.NUMERIC(5, 4), default=0.0000),
        sa.Column('discount_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('line_total', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('vat_code', sa.String(1), default='S'),
        sa.Column('vat_rate', postgresql.NUMERIC(5, 4), default=0.0000),
        sa.Column('vat_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('quantity_shipped', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('quantity_invoiced', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('delivery_date', sa.DateTime()),
        sa.Column('notes', sa.String(200)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['sales_orders.id']),
        sa.UniqueConstraint('order_id', 'line_number', name='uq_sales_order_line')
    )
    
    print("Phase 5: Creating Purchase Transaction tables...")
    
    # Purchase Orders
    op.create_table('purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(12), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(8), nullable=False),
        sa.Column('order_date', sa.DateTime(), nullable=False),
        sa.Column('delivery_date', sa.DateTime()),
        sa.Column('reference', sa.String(30)),
        sa.Column('supplier_reference', sa.String(30)),
        sa.Column('buyer_code', sa.String(20)),
        sa.Column('delivery_address', sa.String(300)),
        sa.Column('payment_terms', sa.String(20)),
        sa.Column('currency_code', sa.String(3), default='USD'),
        sa.Column('exchange_rate', postgresql.NUMERIC(10, 6), default=1.000000),
        sa.Column('status', sa.Enum('DRAFT', 'APPROVED', 'SENT', 'ACKNOWLEDGED', 'DELIVERED', 'INVOICED', 'CLOSED', 'CANCELLED', name='purchase_order_status_enum'), default='DRAFT'),
        sa.Column('sub_total', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('discount_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('vat_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('total_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('approved_date', sa.DateTime()),
        sa.Column('sent_date', sa.DateTime()),
        sa.Column('acknowledged_date', sa.DateTime()),
        sa.Column('completed_date', sa.DateTime()),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_number'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'])
    )
    op.create_index('idx_purchase_order_supplier', 'purchase_orders', ['supplier_id'])
    op.create_index('idx_purchase_order_date', 'purchase_orders', ['order_date'])
    
    # Purchase Order Lines
    op.create_table('purchase_order_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('stock_code', sa.String(15), nullable=False),
        sa.Column('description', sa.String(60), nullable=False),
        sa.Column('quantity', postgresql.NUMERIC(15, 3), nullable=False),
        sa.Column('unit_cost', postgresql.NUMERIC(15, 4), nullable=False),
        sa.Column('discount_percent', postgresql.NUMERIC(5, 4), default=0.0000),
        sa.Column('discount_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('line_total', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('vat_code', sa.String(1), default='S'),
        sa.Column('vat_rate', postgresql.NUMERIC(5, 4), default=0.0000),
        sa.Column('vat_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('quantity_received', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('quantity_invoiced', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('delivery_date', sa.DateTime()),
        sa.Column('notes', sa.String(200)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['purchase_orders.id']),
        sa.UniqueConstraint('order_id', 'line_number', name='uq_purchase_order_line')
    )
    
    # Goods Receipts
    op.create_table('goods_receipts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receipt_number', sa.String(12), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(8), nullable=False),
        sa.Column('supplier_name', sa.String(60)),
        sa.Column('order_id', sa.Integer()),
        sa.Column('order_number', sa.String(12)),
        sa.Column('receipt_date', sa.DateTime(), nullable=False),
        sa.Column('delivery_note', sa.String(30)),
        sa.Column('carrier', sa.String(30)),
        sa.Column('status', sa.Enum('PENDING', 'PARTIAL', 'RECEIVED', 'CANCELLED', name='goods_receipt_status_enum'), default='PENDING'),
        sa.Column('total_quantity', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('goods_received', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('outstanding_quantity', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('total_value', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('total_amount', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('is_complete', sa.Boolean(), default=False),
        sa.Column('gl_posted', sa.Boolean(), default=False),
        sa.Column('posted_date', sa.DateTime()),
        sa.Column('received_by', sa.String(20)),
        sa.Column('notes', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(20)),
        sa.Column('updated_by', sa.String(20)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('receipt_number'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.ForeignKeyConstraint(['order_id'], ['purchase_orders.id'])
    )
    
    # Goods Receipt Lines
    op.create_table('goods_receipt_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receipt_id', sa.Integer(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('order_line_id', sa.Integer()),
        sa.Column('stock_code', sa.String(15), nullable=False),
        sa.Column('description', sa.String(60), nullable=False),
        sa.Column('quantity_ordered', postgresql.NUMERIC(15, 3), default=0.000),
        sa.Column('quantity_received', postgresql.NUMERIC(15, 3), nullable=False),
        sa.Column('unit_cost', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('line_total', postgresql.NUMERIC(15, 4), default=0.0000),
        sa.Column('location_code', sa.String(10)),
        sa.Column('lot_number', sa.String(20)),
        sa.Column('expiry_date', sa.DateTime()),
        sa.Column('notes', sa.String(200)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['receipt_id'], ['goods_receipts.id']),
        sa.ForeignKeyConstraint(['order_line_id'], ['purchase_order_lines.id']),
        sa.UniqueConstraint('receipt_id', 'line_number', name='uq_goods_receipt_line')
    )
    
    print("Complete schema migration completed successfully!")


def downgrade() -> None:
    """Drop all tables created in this migration"""
    
    # Drop tables in reverse dependency order
    op.drop_table('goods_receipt_lines')
    op.drop_table('goods_receipts')
    op.drop_table('purchase_order_lines')
    op.drop_table('purchase_orders')
    op.drop_table('sales_order_lines')
    op.drop_table('sales_orders')
    op.drop_table('stock_items')
    op.drop_table('suppliers')
    op.drop_table('customers')
    op.drop_table('journal_lines')
    op.drop_table('journal_headers')
    op.drop_table('gl_batches')
    op.drop_table('chart_of_accounts')
    
    # Drop ENUM types
    op.execute("""
        DROP TYPE IF EXISTS irs_posting_status_enum CASCADE;
        DROP TYPE IF EXISTS irs_transaction_type_enum CASCADE;
        DROP TYPE IF EXISTS goods_receipt_status_enum CASCADE;
        DROP TYPE IF EXISTS purchase_order_status_enum CASCADE;
        DROP TYPE IF EXISTS invoice_type_enum CASCADE;
        DROP TYPE IF EXISTS transaction_status_enum CASCADE;
        DROP TYPE IF EXISTS posting_status_enum CASCADE;
        DROP TYPE IF EXISTS journal_type_enum CASCADE;
        DROP TYPE IF EXISTS account_type_enum CASCADE;
    """)