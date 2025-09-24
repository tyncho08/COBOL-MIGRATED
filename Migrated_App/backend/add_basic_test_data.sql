-- Add basic test data for all major tables

-- Insert some basic sales invoices
INSERT INTO sales_invoices (invoice_no, customer_id, invoice_date, due_date, total_amount, tax_amount, amount_paid, created_at) 
VALUES 
    ('SI001', 1, CURRENT_DATE - INTERVAL '15 days', CURRENT_DATE + INTERVAL '15 days', 1200.00, 180.00, 0, CURRENT_TIMESTAMP - INTERVAL '15 days'),
    ('SI002', 2, CURRENT_DATE - INTERVAL '10 days', CURRENT_DATE + INTERVAL '20 days', 850.00, 127.50, 850.00, CURRENT_TIMESTAMP - INTERVAL '10 days'),
    ('SI003', 3, CURRENT_DATE - INTERVAL '7 days', CURRENT_DATE + INTERVAL '23 days', 2100.00, 315.00, 1000.00, CURRENT_TIMESTAMP - INTERVAL '7 days'),
    ('SI004', 1, CURRENT_DATE - INTERVAL '3 days', CURRENT_DATE + INTERVAL '27 days', 675.00, 101.25, 0, CURRENT_TIMESTAMP - INTERVAL '3 days'),
    ('SI005', 4, CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE + INTERVAL '29 days', 3200.00, 480.00, 0, CURRENT_TIMESTAMP - INTERVAL '1 day')
ON CONFLICT (invoice_no) DO NOTHING;

-- Insert some basic purchase orders
INSERT INTO purchase_orders (supplier_id, order_date, total_amount, created_by, created_at) 
VALUES 
    (1, CURRENT_DATE - INTERVAL '12 days', 2500.00, 1, CURRENT_TIMESTAMP - INTERVAL '12 days'),
    (2, CURRENT_DATE - INTERVAL '9 days', 1800.00, 1, CURRENT_TIMESTAMP - INTERVAL '9 days'),
    (3, CURRENT_DATE - INTERVAL '6 days', 3200.00, 1, CURRENT_TIMESTAMP - INTERVAL '6 days'),
    (1, CURRENT_DATE - INTERVAL '4 days', 950.00, 1, CURRENT_TIMESTAMP - INTERVAL '4 days'),
    (4, CURRENT_DATE - INTERVAL '2 days', 4100.00, 1, CURRENT_TIMESTAMP - INTERVAL '2 days'),
    (2, CURRENT_DATE, 1750.00, 1, CURRENT_TIMESTAMP);

-- Insert some basic purchase invoices
INSERT INTO purchase_invoices (invoice_no, supplier_id, invoice_date, due_date, total_amount, tax_amount, amount_paid, created_at)
VALUES 
    ('PI001', 1, CURRENT_DATE - INTERVAL '14 days', CURRENT_DATE + INTERVAL '16 days', 2500.00, 375.00, 2875.00, CURRENT_TIMESTAMP - INTERVAL '14 days'),
    ('PI002', 2, CURRENT_DATE - INTERVAL '11 days', CURRENT_DATE + INTERVAL '19 days', 1800.00, 270.00, 0, CURRENT_TIMESTAMP - INTERVAL '11 days'),
    ('PI003', 3, CURRENT_DATE - INTERVAL '8 days', CURRENT_DATE + INTERVAL '22 days', 3200.00, 480.00, 1500.00, CURRENT_TIMESTAMP - INTERVAL '8 days'),
    ('PI004', 1, CURRENT_DATE - INTERVAL '5 days', CURRENT_DATE + INTERVAL '25 days', 950.00, 142.50, 0, CURRENT_TIMESTAMP - INTERVAL '5 days'),
    ('PI005', 4, CURRENT_DATE - INTERVAL '3 days', CURRENT_DATE + INTERVAL '27 days', 4100.00, 615.00, 0, CURRENT_TIMESTAMP - INTERVAL '3 days')
ON CONFLICT (invoice_no) DO NOTHING;

-- Verify the data
SELECT 'sales_orders' as table_name, COUNT(*) as record_count FROM sales_orders
UNION ALL
SELECT 'sales_invoices' as table_name, COUNT(*) as record_count FROM sales_invoices
UNION ALL
SELECT 'purchase_orders' as table_name, COUNT(*) as record_count FROM purchase_orders  
UNION ALL
SELECT 'purchase_invoices' as table_name, COUNT(*) as record_count FROM purchase_invoices
ORDER BY table_name;

-- Show sample data from each table
SELECT 'Sales Orders Sample:' as info;
SELECT id, order_date, customer_id, total_amount FROM sales_orders LIMIT 3;

SELECT 'Sales Invoices Sample:' as info;
SELECT id, invoice_no, customer_id, invoice_date, total_amount FROM sales_invoices LIMIT 3;

SELECT 'Purchase Orders Sample:' as info;
SELECT id, supplier_id, order_date, total_amount FROM purchase_orders LIMIT 3;

SELECT 'Purchase Invoices Sample:' as info;
SELECT id, invoice_no, supplier_id, invoice_date, total_amount FROM purchase_invoices LIMIT 3;