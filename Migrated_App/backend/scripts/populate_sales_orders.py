#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from datetime import datetime, date, timedelta
from decimal import Decimal

# Database connection
DATABASE_URL = "postgresql://postgres:password@localhost:5432/acas_migrated"
engine = create_engine(DATABASE_URL)

def populate_sales_orders():
    with engine.connect() as conn:
        # First, check if we have customers to reference
        customers_result = conn.execute(text("SELECT id, customer_code, customer_name FROM customers ORDER BY id LIMIT 10")).fetchall()
        if not customers_result:
            print("No customers found. Please populate customers first.")
            return
        
        # Clear existing sales orders
        conn.execute(text("DELETE FROM sales_orders"))
        conn.commit()
        
        # Insert sample sales orders
        base_date = date.today()
        orders_data = []
        
        for i, customer in enumerate(customers_result):
            # Create 3-4 orders per customer
            for j in range(3 + (i % 2)):  # 3 or 4 orders per customer
                order_date = base_date - timedelta(days=(i * 7) + j * 2)
                delivery_date = order_date + timedelta(days=7 + (j % 3))
                
                order = {
                    'order_no': f'SO{2024:04d}{(i*4+j+1):04d}',
                    'customer_id': customer[0],
                    'order_date': order_date,
                    'delivery_date': delivery_date,
                    'reference': f'REF-{i+1:03d}-{j+1}',
                    'customer_order_no': f'PO{customer[1][-3:]}{j+1:03d}',
                    'delivery_address': f'{customer[2]} Delivery Address',
                    'sales_rep': ['Alice Johnson', 'Bob Wilson', 'Charlie Brown'][i % 3],
                    'payment_terms': ['30 DAYS', '15 DAYS', 'COD'][j % 3],
                    'currency_code': 'USD',
                    'exchange_rate': Decimal('1.00'),
                    'sub_total': Decimal(str(1000 + (i * 250) + (j * 100))),
                    'vat_amount': Decimal(str((1000 + (i * 250) + (j * 100)) * 0.15)),  # 15% VAT
                    'total_amount': Decimal(str((1000 + (i * 250) + (j * 100)) * 1.15)),
                    'status': ['DRAFT', 'CONFIRMED', 'PROCESSING', 'SHIPPED'][j % 4],
                    'notes': f'Sales order {i+1}-{j+1} for {customer[2]}',
                    'created_by': 1,
                    'created_at': datetime.now() - timedelta(days=(i * 7) + j * 2),
                    'approved_by': 1 if j > 0 else None,
                    'approved_at': (datetime.now() - timedelta(days=(i * 7) + j * 2 - 1)) if j > 0 else None
                }
                orders_data.append(order)
        
        # Insert sales orders
        insert_query = text("""
            INSERT INTO sales_orders (
                order_no, customer_id, order_date, delivery_date, reference,
                customer_order_no, delivery_address, sales_rep, payment_terms,
                currency_code, exchange_rate, sub_total, vat_amount, total_amount,
                status, notes, created_by, created_at, approved_by, approved_at
            ) VALUES (
                :order_no, :customer_id, :order_date, :delivery_date, :reference,
                :customer_order_no, :delivery_address, :sales_rep, :payment_terms,
                :currency_code, :exchange_rate, :sub_total, :vat_amount, :total_amount,
                :status, :notes, :created_by, :created_at, :approved_by, :approved_at
            )
        """)
        
        for order in orders_data:
            conn.execute(insert_query, order)
        
        conn.commit()
        print(f"Successfully populated {len(orders_data)} sales orders")
        
        # Verify the data
        result = conn.execute(text("""
            SELECT COUNT(*) as total_orders,
                   AVG(total_amount) as avg_total,
                   COUNT(DISTINCT customer_id) as unique_customers
            FROM sales_orders
        """)).fetchone()
        
        print(f"Verification: {result[0]} orders, average total: ${result[1]:.2f}, {result[2]} customers")

if __name__ == "__main__":
    populate_sales_orders()