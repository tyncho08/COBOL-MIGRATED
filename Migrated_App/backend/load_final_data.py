#!/usr/bin/env python3
"""
FINAL DATA LOADER - Simplified with correct field mappings
"""
import psycopg2
from datetime import datetime, timedelta
import random

DATABASE_URL = "postgresql://acas_user:secure-password-change-in-production@localhost:5432/acas_db"

def load_data():
    """Load complete data for all tables"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        print("🚀 LOADING FINAL DATA...")
        print("=" * 60)
        
        # Clean existing data
        print("\n🗑️  Cleaning existing data...")
        tables = [
            'payment_allocations', 'customer_payments', 'sales_invoice_lines', 'sales_invoices',
            'sales_order_lines', 'sales_orders', 'goods_receipt_lines', 'goods_receipts',
            'purchase_invoice_lines', 'purchase_invoices', 'purchase_order_lines', 'purchase_orders',
            'supplier_payments', 'stock_movements', 'journal_entries', 
            'customers', 'suppliers', 'stock_items'
        ]
        for table in tables:
            cur.execute(f"DELETE FROM {table}")
        conn.commit()
        print("✅ Cleaned all data")
        
        # 1. CUSTOMERS
        print("\n📝 Loading Customers...")
        customers = []
        for i in range(10):
            cur.execute("""
                INSERT INTO customers (
                    customer_no, name, address_line1, postal_code, phone, email, 
                    credit_limit, current_balance, ytd_sales, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"CUST{str(i+1).zfill(3)}", f"Customer {i+1} Company",
                f"{100+i} Main Street", f"{10001+i}", f"555-{1000+i}",
                f"customer{i+1}@example.com", 50000.00, 
                round(random.uniform(0, 10000), 2),
                round(random.uniform(10000, 100000), 2), datetime.now()
            ))
            customers.append(cur.fetchone()[0])
        print(f"✅ Loaded {len(customers)} customers")
        
        # 2. SUPPLIERS  
        print("\n📝 Loading Suppliers...")
        suppliers = []
        for i in range(8):
            cur.execute("""
                INSERT INTO suppliers (
                    supplier_no, name, address_line1, postal_code, phone, email,
                    current_balance, ytd_purchases, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"SUPP{str(i+1).zfill(3)}", f"Supplier {i+1} Inc",
                f"{200+i} Supply Road", f"{20001+i}", f"555-{2000+i}",
                f"supplier{i+1}@example.com",
                round(random.uniform(0, 20000), 2),
                round(random.uniform(20000, 200000), 2), datetime.now()
            ))
            suppliers.append(cur.fetchone()[0])
        print(f"✅ Loaded {len(suppliers)} suppliers")
        
        # 3. STOCK ITEMS
        print("\n📝 Loading Stock Items...")
        stock_items = []
        for i in range(20):
            cur.execute("""
                INSERT INTO stock_items (
                    stock_no, abbreviation, description, unit_of_measure,
                    sell_price_1, unit_cost, qty_on_hand, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"ITEM{str(i+1).zfill(3)}", f"ITM{i+1}",
                f"Product Item {i+1}", "EACH",
                round(random.uniform(50, 500), 2),
                round(random.uniform(25, 250), 2),
                round(random.uniform(10, 1000), 2), datetime.now()
            ))
            stock_items.append(cur.fetchone()[0])
        print(f"✅ Loaded {len(stock_items)} stock items")
        
        # 4. SALES INVOICES with all required fields
        print("\n📝 Loading Sales Invoices...")
        for i in range(50):
            customer_id = random.choice(customers)
            invoice_date = datetime.now() - timedelta(days=random.randint(0, 90))
            
            # Get customer details
            cur.execute("SELECT customer_no, name FROM customers WHERE id = %s", (customer_id,))
            cust_no, cust_name = cur.fetchone()
            
            goods_total = round(random.uniform(100, 5000), 2)
            vat_total = round(goods_total * 0.08, 2)
            gross_total = goods_total + vat_total
            
            paid = random.random() > 0.3
            amount_paid = gross_total if paid else 0
            
            cur.execute("""
                INSERT INTO sales_invoices (
                    invoice_no, invoice_date, customer_id, due_date,
                    subtotal, tax_amount, total_amount, amount_paid, balance_due,
                    invoice_status, created_by, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"INV{str(i+1).zfill(6)}", invoice_date, customer_id,
                invoice_date + timedelta(days=30),
                goods_total, vat_total, gross_total, amount_paid,
                gross_total - amount_paid, 'P' if paid else 'O',
                1, datetime.now()
            ))
            
            invoice_id = cur.fetchone()[0]
            
            # Add invoice lines
            num_lines = random.randint(1, 3)
            for line in range(num_lines):
                stock_id = random.choice(stock_items)
                cur.execute("SELECT stock_no, description FROM stock_items WHERE id = %s", (stock_id,))
                stock_no, desc = cur.fetchone()
                
                cur.execute("""
                    INSERT INTO sales_invoice_lines (
                        invoice_id, line_no, stock_item_id, description,
                        quantity, unit_price, line_total, tax_amount
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    invoice_id, line + 1, stock_id, desc,
                    random.randint(1, 10), goods_total / num_lines,
                    goods_total / num_lines, vat_total / num_lines
                ))
        print("✅ Loaded 50 sales invoices with lines")
        
        # 5. CUSTOMER PAYMENTS
        print("\n📝 Loading Customer Payments...")
        for i in range(40):
            customer_id = random.choice(customers)
            cur.execute("SELECT customer_no FROM customers WHERE id = %s", (customer_id,))
            cust_no = cur.fetchone()[0]
            
            payment_amount = round(random.uniform(500, 10000), 2)
            cur.execute("""
                INSERT INTO customer_payments (
                    payment_number, payment_date, customer_id, customer_code,
                    payment_method, payment_amount, allocated_amount, unallocated_amount,
                    reference, created_by, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"PAY{str(i+1).zfill(6)}", datetime.now() - timedelta(days=random.randint(0, 60)),
                customer_id, cust_no, random.choice(['CHECK', 'TRANSFER', 'CARD']),
                payment_amount, 0, payment_amount, f"REF-{random.randint(10000, 99999)}",
                '1', datetime.now()
            ))
        print("✅ Loaded 40 customer payments")
        
        # 6. SALES ORDERS
        print("\n📝 Loading Sales Orders...")
        for i in range(35):
            customer_id = random.choice(customers)
            cur.execute("SELECT customer_no, name FROM customers WHERE id = %s", (customer_id,))
            cust_no, cust_name = cur.fetchone()
            
            subtotal = round(random.uniform(100, 5000), 2)
            tax_amount = round(subtotal * 0.08, 2)
            total_amount = subtotal + tax_amount
            
            cur.execute("""
                INSERT INTO sales_orders (
                    order_no, customer_id, order_date, order_status,
                    subtotal, tax_amount, total_amount, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                f"SO{str(i+1).zfill(6)}", customer_id,
                datetime.now() - timedelta(days=random.randint(0, 30)),
                random.choice(['O', 'C', 'S']),  # O=Open, C=Complete, S=Shipped
                subtotal, tax_amount, total_amount, datetime.now()
            ))
            
            order_id = cur.fetchone()[0]
            
            # Add order lines
            num_lines = random.randint(1, 3)
            for line in range(num_lines):
                stock_id = random.choice(stock_items)
                cur.execute("SELECT stock_no, description FROM stock_items WHERE id = %s", (stock_id,))
                stock_no, desc = cur.fetchone()
                
                cur.execute("""
                    INSERT INTO sales_order_lines (
                        order_id, line_no, stock_item_id, description, quantity,
                        unit_price, line_total
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    order_id, line + 1, stock_id, desc, random.randint(1, 10),
                    subtotal / num_lines, subtotal / num_lines
                ))
        print("✅ Loaded 35 sales orders with lines")
        
        # 7. PURCHASE ORDERS
        print("\n📝 Loading Purchase Orders...")
        for i in range(25):
            supplier_id = random.choice(suppliers)
            
            subtotal = round(random.uniform(500, 10000), 2)
            tax_amount = round(subtotal * 0.08, 2)
            total_amount = subtotal + tax_amount
            
            cur.execute("""
                INSERT INTO purchase_orders (
                    po_no, supplier_id, po_date, po_status,
                    subtotal, tax_amount, total_amount, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"PO{str(i+1).zfill(6)}", supplier_id,
                datetime.now() - timedelta(days=random.randint(0, 45)),
                random.choice(['O', 'A', 'R']),  # O=Open, A=Approved, R=Received
                subtotal, tax_amount, total_amount, datetime.now()
            ))
        print("✅ Loaded 25 purchase orders")
        
        # 8. GOODS RECEIPTS
        print("\n📝 Loading Goods Receipts...")
        for i in range(20):
            supplier_id = random.choice(suppliers)
            
            cur.execute("""
                INSERT INTO goods_receipts (
                    receipt_number, supplier_id, receipt_date, receipt_status,
                    received_by, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                f"GR{str(i+1).zfill(6)}", supplier_id,
                datetime.now() - timedelta(days=random.randint(0, 30)),
                random.choice(['PENDING', 'RECEIVED', 'INSPECTED', 'POSTED']),
                'warehouse', datetime.now()
            ))
        print("✅ Loaded 20 goods receipts")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DATA LOAD COMPLETE!")
        print("=" * 60)
        tables_to_check = [
            'customers', 'suppliers', 'stock_items', 'sales_invoices',
            'customer_payments', 'sales_orders', 'purchase_orders', 'goods_receipts'
        ]
        
        for table in tables_to_check:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"{table:.<30} {count:>5} records")
            
        print("\n✅ All data loaded successfully!")
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    load_data()