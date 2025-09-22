#!/usr/bin/env python3
"""
Database Initialization Script
Creates the ACAS database schema and loads initial data
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from app.config.database import Base, engine
from app.config.settings import settings
from app.config.security import get_password_hash
from app.models import *
from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def create_initial_data():
    """Create initial system data"""
    with Session(engine) as session:
        # Check if data already exists
        existing_config = session.query(SystemConfig).first()
        if existing_config:
            print("⚠ Initial data already exists, skipping...")
            return
        
        print("Creating initial data...")
        
        # 1. Create System Configuration
        system_config = SystemConfig(
            company_name="ACAS Demo Company",
            company_address1="123 Main Street",
            company_address2="Suite 100",
            company_address3="New York, NY",
            company_postcode="10001",
            company_phone="(555) 123-4567",
            company_email="info@acasdemo.com",
            company_registration="12345678",
            vat_registration="VAT123456",
            fiscal_year_start=1,
            current_period=1,
            periods_per_year=12,
            sales_ledger_enabled=True,
            purchase_ledger_enabled=True,
            stock_control_enabled=True,
            general_ledger_enabled=True,
            irs_enabled=True,
            vat_enabled=True,
            default_vat_rate=Decimal("20.0"),
            base_currency="USD",
            multi_currency_enabled=True,
            force_credit_limit=True,
            allow_negative_stock=False,
            auto_generate_gl_postings=True,
            next_invoice_number=1000,
            next_order_number=1000,
            next_payment_number=1000,
            next_batch_number=1,
            updated_by="SYSTEM",
        )
        session.add(system_config)
        
        # 2. Create default admin user
        admin_user = User(
            username="admin",
            full_name="System Administrator",
            email="admin@acasdemo.com",
            hashed_password=get_password_hash("admin123"),  # Change in production!
            is_active=True,
            is_superuser=True,
            user_level=9,  # Maximum permission level
            module_access={
                "SL": 9,  # Sales Ledger - Full access
                "PL": 9,  # Purchase Ledger - Full access
                "ST": 9,  # Stock Control - Full access
                "GL": 9,  # General Ledger - Full access
                "IRS": 9, # IRS System - Full access
                "SYS": 9  # System Admin - Full access
            },
            login_count=0,
        )
        session.add(admin_user)
        
        # 3. Create demo user
        demo_user = User(
            username="demo",
            full_name="Demo User",
            email="demo@acasdemo.com",
            hashed_password=get_password_hash("demo123"),
            is_active=True,
            is_superuser=False,
            user_level=2,  # Operator level
            module_access={
                "SL": 2,  # Sales Ledger - Operator
                "PL": 2,  # Purchase Ledger - Operator
                "ST": 1,  # Stock Control - Enquiry only
                "GL": 1,  # General Ledger - Enquiry only
                "IRS": 0, # IRS System - No access
                "SYS": 0  # System Admin - No access
            },
            login_count=0,
        )
        session.add(demo_user)
        
        # 4. Create current financial period
        current_year = datetime.now().year
        for period in range(1, 13):
            period_start = datetime(current_year, period, 1)
            # Calculate period end (last day of month)
            if period == 12:
                period_end = datetime(current_year, 12, 31)
            else:
                period_end = datetime(current_year, period + 1, 1) - timedelta(days=1)
            
            company_period = CompanyPeriod(
                period_number=period,
                year_number=current_year,
                start_date=period_start,
                end_date=period_end,
                is_open=True if period <= 2 else False,  # First 2 periods open
                is_current=True if period == 1 else False,
                gl_closed=False,
                sl_closed=False,
                pl_closed=False,
                stock_closed=False,
            )
            session.add(company_period)
        
        # 5. Create system parameters
        parameters = [
            # Sales Ledger Parameters
            ("SL", "INVOICE_PREFIX", "INV", "STRING", "Invoice number prefix"),
            ("SL", "CREDIT_NOTE_PREFIX", "CN", "STRING", "Credit note prefix"),
            ("SL", "STATEMENT_DAY", "25", "NUMBER", "Day of month for statements"),
            
            # Purchase Ledger Parameters
            ("PL", "ORDER_PREFIX", "PO", "STRING", "Purchase order prefix"),
            ("PL", "AUTO_MATCH_TOLERANCE", "0.01", "NUMBER", "Auto-match tolerance amount"),
            
            # Stock Control Parameters
            ("ST", "AUTO_REORDER", "TRUE", "BOOLEAN", "Enable automatic reordering"),
            ("ST", "STOCK_TAKE_VARIANCE", "5.0", "NUMBER", "Acceptable stock take variance %"),
            
            # General Ledger Parameters
            ("GL", "RETAINED_EARNINGS_ACCOUNT", "3000.0000", "STRING", "Retained earnings GL account"),
            ("GL", "SUSPENSE_ACCOUNT", "9999.0000", "STRING", "Suspense GL account"),
            
            # System Parameters
            ("SYS", "PASSWORD_MIN_LENGTH", "8", "NUMBER", "Minimum password length"),
            ("SYS", "SESSION_TIMEOUT", "30", "NUMBER", "Session timeout in minutes"),
            ("SYS", "BACKUP_RETENTION_DAYS", "30", "NUMBER", "Backup retention period"),
        ]
        
        for module, name, value, param_type, description in parameters:
            param = SystemParameter(
                module_code=module,
                parameter_name=name,
                parameter_value=value,
                parameter_type=param_type,
                description=description,
                is_encrypted=False,
                updated_by="SYSTEM",
            )
            session.add(param)
        
        # 6. Create demo customers
        demo_customers = [
            {
                "customer_code": "CUST001",
                "customer_name": "ABC Corporation",
                "address_line1": "456 Business Ave",
                "address_line2": "Floor 5",
                "address_line3": "Chicago, IL",
                "postcode": "60601",
                "phone_number": "(312) 555-0001",
                "email_address": "ap@abccorp.com",
                "credit_limit": Decimal("10000.00"),
                "payment_terms": 30,
                "vat_registration": "VAT789012",
                "analysis_code1": "CORP",
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST002",
                "customer_name": "XYZ Industries",
                "address_line1": "789 Industrial Way",
                "address_line2": "",
                "address_line3": "Detroit, MI",
                "postcode": "48201",
                "phone_number": "(313) 555-0002",
                "email_address": "purchasing@xyzind.com",
                "credit_limit": Decimal("25000.00"),
                "payment_terms": 45,
                "discount_percentage": Decimal("2.5"),
                "analysis_code1": "IND",
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
        ]
        
        for cust_data in demo_customers:
            customer = Customer(**cust_data)
            session.add(customer)
        
        # 7. Create demo stock items
        demo_stock = [
            {
                "stock_code": "WIDGET-001",
                "abbreviated_code": "WDG001",
                "description": "Standard Widget - Blue",
                "unit_of_measure": "EACH",
                "category_code": "WIDGETS",
                "quantity_on_hand": Decimal("100.000"),
                "reorder_level": Decimal("25.000"),
                "reorder_quantity": Decimal("50.000"),
                "cost_method": "AVERAGE",
                "standard_cost": Decimal("10.00"),
                "average_cost": Decimal("10.00"),
                "selling_price1": Decimal("15.00"),
                "selling_price2": Decimal("14.00"),
                "selling_price3": Decimal("13.00"),
                "vat_code": "S",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "stock_code": "SERVICE-001",
                "abbreviated_code": "SVC001",
                "description": "Professional Services - 1 Hour",
                "unit_of_measure": "HOUR",
                "category_code": "SERVICES",
                "is_stocked": False,
                "standard_cost": Decimal("75.00"),
                "selling_price1": Decimal("125.00"),
                "vat_code": "S",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
        ]
        
        for stock_data in demo_stock:
            stock = StockItem(**stock_data)
            session.add(stock)
        
        # Commit all changes
        session.commit()
        print("✓ Initial data created successfully")
        
        # Print summary
        print("\n=== Initial Setup Complete ===")
        print("Admin User: admin / admin123")
        print("Demo User: demo / demo123")
        print("Demo Customers: CUST001, CUST002")
        print("Demo Stock Items: WIDGET-001, SERVICE-001")
        print("\nIMPORTANT: Change default passwords in production!")


def main():
    """Main initialization function"""
    print("ACAS Database Initialization")
    print("=" * 40)
    
    try:
        # Create tables
        create_tables()
        
        # Load initial data
        create_initial_data()
        
        print("\n✓ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Import timedelta here to avoid circular import
    from datetime import timedelta
    main()