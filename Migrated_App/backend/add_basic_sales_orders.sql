-- Insert basic sales orders data
INSERT INTO sales_orders (order_no, customer_id, order_date, total_amount, created_by, created_at, status) 
VALUES 
    ('SO001', 1, CURRENT_DATE - INTERVAL '10 days', 1500.00, 1, CURRENT_TIMESTAMP - INTERVAL '10 days', 'CONFIRMED'),
    ('SO002', 2, CURRENT_DATE - INTERVAL '8 days', 2300.00, 1, CURRENT_TIMESTAMP - INTERVAL '8 days', 'PROCESSING'),
    ('SO003', 3, CURRENT_DATE - INTERVAL '6 days', 850.00, 1, CURRENT_TIMESTAMP - INTERVAL '6 days', 'SHIPPED'),
    ('SO004', 1, CURRENT_DATE - INTERVAL '4 days', 3200.00, 1, CURRENT_TIMESTAMP - INTERVAL '4 days', 'CONFIRMED'),
    ('SO005', 4, CURRENT_DATE - INTERVAL '2 days', 675.00, 1, CURRENT_TIMESTAMP - INTERVAL '2 days', 'DRAFT'),
    ('SO006', 2, CURRENT_DATE - INTERVAL '1 day', 1890.00, 1, CURRENT_TIMESTAMP - INTERVAL '1 day', 'CONFIRMED'),
    ('SO007', 5, CURRENT_DATE, 4100.00, 1, CURRENT_TIMESTAMP, 'DRAFT')
ON CONFLICT (order_no) DO NOTHING;

-- Verify the data was inserted
SELECT 
    COUNT(*) as total_orders,
    MIN(order_date) as oldest_order,
    MAX(order_date) as newest_order,
    SUM(total_amount) as total_value
FROM sales_orders;