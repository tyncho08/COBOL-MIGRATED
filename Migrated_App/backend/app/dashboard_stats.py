"""
Dashboard statistics function with proper database handling
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_dashboard_statistics(db: Session):
    """Get real dashboard statistics from database"""
    stats = {
        "totalPurchaseOrders": 0,
        "pendingApprovals": 0,
        "stockItems": 0,
        "lowStockItems": 0,
        "totalSuppliers": 0,
        "activeSuppliers": 0,
        "openPeriods": 1,
        "journalEntries": 0,
        "totalSalesOrders": 0,
        "totalSalesInvoices": 0,
        "outstandingInvoices": 0,
        "totalCustomers": 0
    }
    
    # Use separate connection for each query to avoid transaction issues
    
    # Get customers count (we know this table exists)
    try:
        result = db.execute(text("SELECT COUNT(*) FROM customers"))
        stats["totalCustomers"] = result.scalar() or 0
        db.commit()  # Commit to clear any transaction state
    except Exception as e:
        logger.debug(f"Customers count error: {e}")
        db.rollback()
    
    # Get purchase orders count
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'purchase_orders'
        """))
        if result.scalar() > 0:
            count_result = db.execute(text("SELECT COUNT(*) FROM purchase_orders"))
            stats["totalPurchaseOrders"] = count_result.scalar() or 0
            
            # Get pending approvals
            pending_result = db.execute(text("SELECT COUNT(*) FROM purchase_orders WHERE status = 'PENDING'"))
            stats["pendingApprovals"] = pending_result.scalar() or 0
        db.commit()
    except Exception as e:
        logger.debug(f"Purchase orders error: {e}")
        db.rollback()
    
    # Get stock items count
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'stock_items'
        """))
        if result.scalar() > 0:
            count_result = db.execute(text("SELECT COUNT(*) FROM stock_items"))
            stats["stockItems"] = count_result.scalar() or 0
            
            # Get low stock items
            low_stock_result = db.execute(text("""
                SELECT COUNT(*) FROM stock_items 
                WHERE quantity_on_hand < reorder_level
            """))
            stats["lowStockItems"] = low_stock_result.scalar() or 0
        db.commit()
    except Exception as e:
        logger.debug(f"Stock items error: {e}")
        db.rollback()
    
    # Get suppliers count
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'suppliers'
        """))
        if result.scalar() > 0:
            count_result = db.execute(text("SELECT COUNT(*) FROM suppliers"))
            stats["totalSuppliers"] = count_result.scalar() or 0
            
            # Get active suppliers
            active_result = db.execute(text("SELECT COUNT(*) FROM suppliers WHERE is_active = true"))
            stats["activeSuppliers"] = active_result.scalar() or 0
        db.commit()
    except Exception as e:
        logger.debug(f"Suppliers error: {e}")
        db.rollback()
    
    # Get open periods
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'accounting_periods'
        """))
        if result.scalar() > 0:
            open_result = db.execute(text("SELECT COUNT(*) FROM accounting_periods WHERE is_closed = false"))
            stats["openPeriods"] = open_result.scalar() or 1
        db.commit()
    except Exception as e:
        logger.debug(f"Periods error: {e}")
        db.rollback()
    
    # Get journal entries count
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'journal_entries'
        """))
        if result.scalar() > 0:
            count_result = db.execute(text("SELECT COUNT(*) FROM journal_entries"))
            stats["journalEntries"] = count_result.scalar() or 0
        db.commit()
    except Exception as e:
        logger.debug(f"Journal entries error: {e}")
        db.rollback()
    
    # Get sales orders count
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'sales_orders'
        """))
        if result.scalar() > 0:
            count_result = db.execute(text("SELECT COUNT(*) FROM sales_orders"))
            stats["totalSalesOrders"] = count_result.scalar() or 0
        db.commit()
    except Exception as e:
        logger.debug(f"Sales orders error: {e}")
        db.rollback()
    
    # Get sales invoices count
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'sales_invoices'
        """))
        if result.scalar() > 0:
            count_result = db.execute(text("SELECT COUNT(*) FROM sales_invoices"))
            stats["totalSalesInvoices"] = count_result.scalar() or 0
            
            # Get outstanding invoices
            outstanding_result = db.execute(text("""
                SELECT COUNT(*) FROM sales_invoices 
                WHERE is_paid = false
            """))
            stats["outstandingInvoices"] = outstanding_result.scalar() or 0
        db.commit()
    except Exception as e:
        logger.debug(f"Sales invoices error: {e}")
        db.rollback()
    
    # Get recent activity
    recent_activity = []
    
    # Try to get purchase order activity
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'purchase_orders'
        """))
        if result.scalar() > 0:
            po_activity = db.execute(text("""
                SELECT 'purchase_order' as type, 
                       'Purchase Order ' || order_no || ' created' as description,
                       created_at as timestamp,
                       status
                FROM purchase_orders
                ORDER BY created_at DESC
                LIMIT 2
            """)).fetchall()
            
            for activity in po_activity:
                recent_activity.append({
                    "id": f"po_{len(recent_activity)+1}",
                    "type": activity.type,
                    "description": activity.description,
                    "timestamp": activity.timestamp.isoformat() if activity.timestamp else datetime.now().isoformat(),
                    "status": activity.status.lower() if activity.status else "pending"
                })
        db.commit()
    except Exception as e:
        logger.debug(f"PO activity error: {e}")
        db.rollback()
    
    # Try to get sales invoice activity
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'sales_invoices'
        """))
        if result.scalar() > 0:
            si_activity = db.execute(text("""
                SELECT 'sales_invoice' as type,
                       'Sales Invoice ' || invoice_no || ' created' as description,
                       created_at as timestamp,
                       'posted' as status
                FROM sales_invoices
                ORDER BY created_at DESC
                LIMIT 2
            """)).fetchall()
            
            for activity in si_activity:
                recent_activity.append({
                    "id": f"inv_{len(recent_activity)+1}",
                    "type": activity.type,
                    "description": activity.description,
                    "timestamp": activity.timestamp.isoformat() if activity.timestamp else datetime.now().isoformat(),
                    "status": activity.status
                })
        db.commit()
    except Exception as e:
        logger.debug(f"SI activity error: {e}")
        db.rollback()
    
    # If no recent activity found, add a default entry
    if not recent_activity:
        recent_activity.append({
            "id": "default_1",
            "type": "system",
            "description": "System started",
            "timestamp": datetime.now().isoformat(),
            "status": "active"
        })
    
    return {
        "stats": stats,
        "recentActivity": recent_activity,
        "generatedAt": datetime.now().isoformat()
    }