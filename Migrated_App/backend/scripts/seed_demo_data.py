#!/usr/bin/env python3
"""
Comprehensive Demo Data Seeding Script for ACAS
Creates realistic business data for all modules to replace frontend mock data
"""
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from app.config.database import Base, engine
from app.config.settings import settings
from app.models import *
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
import random


def seed_comprehensive_data():
    """Create comprehensive business data for all modules"""
    with Session(engine) as session:
        print("🌱 Starting comprehensive data seeding...")
        
        # Check if we already have substantial data
        customer_count = session.query(Customer).count()
        if customer_count > 15:
            print("⚠ Substantial data already exists. Use --force to override.")
            return
        
        # 1. Create additional customers (beyond the 2 from init_db.py)
        additional_customers = [
            {
                "customer_code": "CUST003",
                "customer_name": "TechSolutions Inc",
                "address_line1": "567 Technology Drive",
                "address_line2": "Building A",
                "address_line3": "San Francisco, CA",
                "postcode": "94105",
                "phone_number": "(415) 555-0003",
                "email_address": "billing@techsolutions.com",
                "credit_limit": Decimal("50000.00"),
                "payment_terms": 30,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST004",
                "customer_name": "Global Manufacturing",
                "address_line1": "890 Industrial Blvd",
                "address_line2": "Suite 200",
                "address_line3": "Houston, TX",
                "postcode": "77001",
                "phone_number": "(713) 555-0004",
                "email_address": "ap@globalmfg.com",
                "credit_limit": Decimal("75000.00"),
                "payment_terms": 45,
                "discount_percentage": Decimal("3.0"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST005",
                "customer_name": "Retail Mart Chain",
                "address_line1": "123 Commerce Street",
                "address_line2": "",
                "address_line3": "Miami, FL",
                "postcode": "33101",
                "phone_number": "(305) 555-0005",
                "email_address": "finance@retailmart.com",
                "credit_limit": Decimal("100000.00"),
                "payment_terms": 60,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST006",
                "customer_name": "Professional Services LLC",
                "address_line1": "654 Corporate Pkwy",
                "address_line2": "Suite 500",
                "address_line3": "Dallas, TX",
                "postcode": "75201",
                "phone_number": "(214) 555-0006",
                "email_address": "billing@proservices.com",
                "credit_limit": Decimal("40000.00"),
                "payment_terms": 45,
                "discount_percentage": Decimal("2.0"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST007",
                "customer_name": "Manufacturing Plus Co",
                "address_line1": "987 Production Way",
                "address_line2": "Unit 12",
                "address_line3": "Cleveland, OH",
                "postcode": "44101",
                "phone_number": "(216) 555-0007",
                "email_address": "finance@mfgplus.com",
                "credit_limit": Decimal("80000.00"),
                "payment_terms": 30,
                "discount_percentage": Decimal("4.0"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST008",
                "customer_name": "Tech Startup Labs",
                "address_line1": "147 Innovation Hub",
                "address_line2": "Incubator B",
                "address_line3": "Austin, TX",
                "postcode": "78701",
                "phone_number": "(512) 555-0008",
                "email_address": "billing@techstartup.com",
                "credit_limit": Decimal("15000.00"),
                "payment_terms": 15,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST009",
                "customer_name": "Enterprise Solutions Corp",
                "address_line1": "258 Corporate Dr",
                "address_line2": "Tower 1",
                "address_line3": "Boston, MA",
                "postcode": "02101",
                "phone_number": "(617) 555-0009",
                "email_address": "ar@enterprise.com",
                "credit_limit": Decimal("120000.00"),
                "payment_terms": 45,
                "discount_percentage": Decimal("3.5"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST010",
                "customer_name": "Local Retailers Co",
                "address_line1": "369 Main Street",
                "address_line2": "",
                "address_line3": "Portland, OR",
                "postcode": "97201",
                "phone_number": "(503) 555-0010",
                "email_address": "accounting@localretail.com",
                "credit_limit": Decimal("20000.00"),
                "payment_terms": 30,
                "discount_percentage": Decimal("1.0"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "customer_code": "CUST011",
                "customer_name": "Distribution Network Inc",
                "address_line1": "741 Logistics Ave",
                "address_line2": "Warehouse C",
                "address_line3": "Memphis, TN",
                "postcode": "38101",
                "phone_number": "(901) 555-0011",
                "email_address": "finance@distribution.com",
                "credit_limit": Decimal("90000.00"),
                "payment_terms": 60,
                "discount_percentage": Decimal("4.5"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
        ]
        
        for cust_data in additional_customers:
            customer = Customer(**cust_data)
            session.add(customer)
        
        # 2. Create additional suppliers
        suppliers = [
            {
                "supplier_code": "SUPP001",
                "supplier_name": "Premium Parts Ltd",
                "address_line1": "234 Supply Chain Ave",
                "address_line2": "Floor 3",
                "address_line3": "Denver, CO",
                "postcode": "80202",
                "phone_number": "(303) 555-1001",
                "email_address": "orders@premiumparts.com",
                "payment_terms": 30,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "supplier_code": "SUPP002",
                "supplier_name": "Quality Components Inc",
                "address_line1": "678 Manufacturing Way",
                "address_line2": "",
                "address_line3": "Portland, OR",
                "postcode": "97201",
                "phone_number": "(503) 555-1002",
                "email_address": "sales@qualitycomp.com",
                "payment_terms": 45,
                "discount_percentage": Decimal("2.0"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "supplier_code": "SUPP003",
                "supplier_name": "Digital Services Pro",
                "address_line1": "901 Tech Park",
                "address_line2": "Building C",
                "address_line3": "Austin, TX",
                "postcode": "78701",
                "phone_number": "(512) 555-1003",
                "email_address": "billing@digitalservices.com",
                "payment_terms": 15,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "supplier_code": "SUPP004",
                "supplier_name": "TechParts Industrial Ltd",
                "address_line1": "456 Industrial Way",
                "address_line2": "Building B",
                "address_line3": "Chicago, IL",
                "postcode": "60601",
                "phone_number": "(312) 555-1004",
                "email_address": "orders@techparts.com",
                "payment_terms": 30,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "supplier_code": "SUPP005",
                "supplier_name": "Global Components Inc",
                "address_line1": "789 Supply Chain Blvd",
                "address_line2": "Suite 300",
                "address_line3": "Atlanta, GA",
                "postcode": "30301",
                "phone_number": "(404) 555-1005",
                "email_address": "sales@globalcomp.com",
                "payment_terms": 45,
                "discount_percentage": Decimal("3.0"),
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "supplier_code": "SUPP006",
                "supplier_name": "Precision Tools Corp",
                "address_line1": "258 Workshop Way",
                "address_line2": "Bay 12",
                "address_line3": "Milwaukee, WI",
                "postcode": "53201",
                "phone_number": "(414) 555-1006",
                "email_address": "orders@precisiontools.com",
                "payment_terms": 45,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "supplier_code": "SUPP007",
                "supplier_name": "Office Solutions Ltd",
                "address_line1": "369 Business Pkwy",
                "address_line2": "Building C",
                "address_line3": "Tampa, FL",
                "postcode": "33601",
                "phone_number": "(813) 555-1007",
                "email_address": "sales@officesolutions.com",
                "payment_terms": 30,
                "currency_code": "USD",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
        ]
        
        for supp_data in suppliers:
            supplier = Supplier(**supp_data)
            session.add(supplier)
        
        # 3. Create additional stock items
        additional_stock = [
            {
                "stock_code": "WIDGET-002",
                "abbreviated_code": "WDG002",
                "description": "Standard Widget - Red",
                "unit_of_measure": "EACH",
                "category_code": "WIDGETS",
                "quantity_on_hand": Decimal("75.000"),
                "reorder_level": Decimal("20.000"),
                "reorder_quantity": Decimal("50.000"),
                "cost_method": "AVERAGE",
                "standard_cost": Decimal("12.00"),
                "average_cost": Decimal("12.00"),
                "selling_price1": Decimal("18.00"),
                "selling_price2": Decimal("17.00"),
                "selling_price3": Decimal("16.00"),
                "vat_code": "S",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "stock_code": "WIDGET-003",
                "abbreviated_code": "WDG003",
                "description": "Premium Widget - Gold",
                "unit_of_measure": "EACH",
                "category_code": "WIDGETS",
                "quantity_on_hand": Decimal("25.000"),
                "reorder_level": Decimal("10.000"),
                "reorder_quantity": Decimal("30.000"),
                "cost_method": "AVERAGE",
                "standard_cost": Decimal("25.00"),
                "average_cost": Decimal("25.00"),
                "selling_price1": Decimal("40.00"),
                "selling_price2": Decimal("38.00"),
                "selling_price3": Decimal("35.00"),
                "vat_code": "S",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "stock_code": "COMP-001",
                "abbreviated_code": "CMP001",
                "description": "Circuit Board Assembly",
                "unit_of_measure": "EACH",
                "category_code": "COMPONENTS",
                "quantity_on_hand": Decimal("150.000"),
                "reorder_level": Decimal("50.000"),
                "reorder_quantity": Decimal("100.000"),
                "cost_method": "FIFO",
                "standard_cost": Decimal("45.00"),
                "average_cost": Decimal("45.00"),
                "selling_price1": Decimal("75.00"),
                "vat_code": "S",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
            {
                "stock_code": "TOOL-001",
                "abbreviated_code": "TL001",
                "description": "Professional Toolkit",
                "unit_of_measure": "SET",
                "category_code": "TOOLS",
                "quantity_on_hand": Decimal("12.000"),
                "reorder_level": Decimal("5.000"),
                "reorder_quantity": Decimal("10.000"),
                "cost_method": "AVERAGE",
                "standard_cost": Decimal("150.00"),
                "average_cost": Decimal("150.00"),
                "selling_price1": Decimal("250.00"),
                "vat_code": "S",
                "created_by": "SYSTEM",
                "updated_by": "SYSTEM",
            },
        ]
        
        for stock_data in additional_stock:
            stock = StockItem(**stock_data)
            session.add(stock)
        
        # 4. Create Chart of Accounts
        accounts = [
            # Assets
            {"account_code": "1000.0000", "account_name": "Cash at Bank", "account_type": "ASSET", "parent_account": None, "is_posting_account": True},
            {"account_code": "1100.0000", "account_name": "Trade Debtors", "account_type": "ASSET", "parent_account": None, "is_posting_account": True},
            {"account_code": "1200.0000", "account_name": "Stock", "account_type": "ASSET", "parent_account": None, "is_posting_account": True},
            {"account_code": "1300.0000", "account_name": "Prepayments", "account_type": "ASSET", "parent_account": None, "is_posting_account": True},
            {"account_code": "1500.0000", "account_name": "Equipment", "account_type": "ASSET", "parent_account": None, "is_posting_account": True},
            
            # Liabilities
            {"account_code": "2000.0000", "account_name": "Trade Creditors", "account_type": "LIABILITY", "parent_account": None, "is_posting_account": True},
            {"account_code": "2100.0000", "account_name": "VAT Control", "account_type": "LIABILITY", "parent_account": None, "is_posting_account": True},
            {"account_code": "2200.0000", "account_name": "Accruals", "account_type": "LIABILITY", "parent_account": None, "is_posting_account": True},
            
            # Equity
            {"account_code": "3000.0000", "account_name": "Retained Earnings", "account_type": "EQUITY", "parent_account": None, "is_posting_account": True},
            {"account_code": "3100.0000", "account_name": "Current Year Earnings", "account_type": "EQUITY", "parent_account": None, "is_posting_account": True},
            
            # Revenue
            {"account_code": "4000.0000", "account_name": "Sales Revenue", "account_type": "REVENUE", "parent_account": None, "is_posting_account": True},
            {"account_code": "4100.0000", "account_name": "Service Revenue", "account_type": "REVENUE", "parent_account": None, "is_posting_account": True},
            
            # Expenses
            {"account_code": "5000.0000", "account_name": "Cost of Sales", "account_type": "EXPENSE", "parent_account": None, "is_posting_account": True},
            {"account_code": "6000.0000", "account_name": "Office Expenses", "account_type": "EXPENSE", "parent_account": None, "is_posting_account": True},
            {"account_code": "6100.0000", "account_name": "Travel Expenses", "account_type": "EXPENSE", "parent_account": None, "is_posting_account": True},
            {"account_code": "6200.0000", "account_name": "Professional Fees", "account_type": "EXPENSE", "parent_account": None, "is_posting_account": True},
            {"account_code": "9999.0000", "account_name": "Suspense Account", "account_type": "ASSET", "parent_account": None, "is_posting_account": True},
        ]
        
        for acc_data in accounts:
            account = ChartOfAccounts(
                **acc_data,
                created_by="SYSTEM",
                updated_by="SYSTEM"
            )
            session.add(account)
        
        # Commit to get IDs
        session.commit()
        
        # 5. Create Purchase Orders
        purchase_orders = []
        for i in range(1, 11):
            po = PurchaseOrder(
                order_number=f"PO{1000 + i:06d}",
                supplier_id=1,  # Will use first supplier
                order_date=datetime.now() - timedelta(days=random.randint(1, 90)),
                delivery_date=datetime.now() + timedelta(days=random.randint(7, 30)),
                order_status="OPEN" if i <= 7 else "CLOSED",
                goods_total=Decimal(str(random.uniform(500, 5000))).quantize(Decimal('0.01')),
                vat_total=Decimal("0.00"),
                gross_total=Decimal(str(random.uniform(500, 5000))).quantize(Decimal('0.01')),
                created_by="SYSTEM",
                updated_by="SYSTEM"
            )
            purchase_orders.append(po)
            session.add(po)
        
        # 6. Create Sales Orders
        sales_orders = []
        for i in range(1, 16):
            so = SalesOrder(
                order_number=f"SO{1000 + i:06d}",
                customer_id=random.randint(1, 3),  # Random customer
                order_date=datetime.now() - timedelta(days=random.randint(1, 60)),
                delivery_date=datetime.now() + timedelta(days=random.randint(3, 21)),
                order_status="OPEN" if i <= 10 else "SHIPPED",
                goods_total=Decimal(str(random.uniform(200, 3000))).quantize(Decimal('0.01')),
                vat_total=Decimal("0.00"),
                gross_total=Decimal(str(random.uniform(200, 3000))).quantize(Decimal('0.01')),
                created_by="SYSTEM",
                updated_by="SYSTEM"
            )
            sales_orders.append(so)
            session.add(so)
        
        # 7. Create Sales Invoices
        sales_invoices = []
        for i in range(1, 21):
            invoice = SalesInvoice(
                invoice_number=f"INV{1000 + i:06d}",
                customer_id=random.randint(1, 3),
                invoice_date=datetime.now() - timedelta(days=random.randint(1, 45)),
                due_date=datetime.now() + timedelta(days=random.randint(0, 60)),
                invoice_type="INVOICE",
                goods_total=Decimal(str(random.uniform(100, 2500))).quantize(Decimal('0.01')),
                vat_total=Decimal("0.00"),
                gross_total=Decimal(str(random.uniform(100, 2500))).quantize(Decimal('0.01')),
                amount_paid=Decimal("0.00") if i <= 15 else Decimal(str(random.uniform(50, 500))).quantize(Decimal('0.01')),
                is_paid=False if i <= 15 else True,
                gl_posted=True,
                invoice_status="POSTED",
                created_by="SYSTEM",
                updated_by="SYSTEM"
            )
            sales_invoices.append(invoice)
            session.add(invoice)
        
        # 8. Create Journal Entries
        journal_entries = []
        for i in range(1, 8):
            je = JournalEntry(
                journal_number=f"JE{1000 + i:06d}",
                journal_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                reference=f"Monthly accrual {i}",
                description=f"Accrual for expenses - Period {i}",
                total_debits=Decimal(str(random.uniform(1000, 5000))).quantize(Decimal('0.01')),
                total_credits=Decimal(str(random.uniform(1000, 5000))).quantize(Decimal('0.01')),
                is_posted=True,
                posted_by="admin",
                posted_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                created_by="SYSTEM",
                updated_by="SYSTEM"
            )
            journal_entries.append(je)
            session.add(je)
        
        # 9. Create Stock Movements (for realistic stock tracking)
        stock_movements = []
        stock_items = session.query(StockItem).all()
        for i, stock_item in enumerate(stock_items[:5]):  # Create movements for first 5 items
            # Incoming movement
            movement_in = StockMovement(
                stock_id=stock_item.id,
                movement_type="RECEIPT",
                reference_number=f"GR{1000 + i:06d}",
                movement_date=datetime.now() - timedelta(days=random.randint(1, 60)),
                quantity=Decimal(str(random.uniform(10, 100))).quantize(Decimal('0.001')),
                unit_cost=stock_item.average_cost,
                total_value=stock_item.average_cost * Decimal(str(random.uniform(10, 100))).quantize(Decimal('0.001')),
                created_by="SYSTEM"
            )
            session.add(movement_in)
            
            # Outgoing movement
            movement_out = StockMovement(
                stock_id=stock_item.id,
                movement_type="ISSUE",
                reference_number=f"SO{1000 + i:06d}",
                movement_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                quantity=Decimal(str(-random.uniform(5, 50))).quantize(Decimal('0.001')),
                unit_cost=stock_item.average_cost,
                total_value=stock_item.average_cost * Decimal(str(-random.uniform(5, 50))).quantize(Decimal('0.001')),
                created_by="SYSTEM"
            )
            session.add(movement_out)
        
        # Commit all data
        session.commit()
        print("✅ Comprehensive demo data created successfully!")
        
        # Print summary
        print("\n=== Demo Data Summary ===")
        print(f"Customers: {session.query(Customer).count()}")
        print(f"Suppliers: {session.query(Supplier).count()}")
        print(f"Stock Items: {session.query(StockItem).count()}")
        print(f"Chart of Accounts: {session.query(ChartOfAccounts).count()}")
        print(f"Purchase Orders: {session.query(PurchaseOrder).count()}")
        print(f"Sales Orders: {session.query(SalesOrder).count()}")
        print(f"Sales Invoices: {session.query(SalesInvoice).count()}")
        print(f"Journal Entries: {session.query(JournalEntry).count()}")
        print(f"Stock Movements: {session.query(StockMovement).count()}")


def main():
    """Main seeding function"""
    print("🌱 ACAS Comprehensive Data Seeding")
    print("=" * 40)
    
    try:
        # Create seed data
        seed_comprehensive_data()
        
        print("\n✅ Data seeding completed successfully!")
        print("\nThe database now contains realistic data for all modules.")
        print("Frontend pages can now connect to backend APIs instead of using mock data.")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()