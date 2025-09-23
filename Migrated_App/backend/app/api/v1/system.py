"""
System API Router
REST endpoints for system administration
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.general_ledger.period_end_service import PeriodEndService

router = APIRouter(prefix="/system", tags=["System Administration"])


# Pydantic models
class PeriodCreate(BaseModel):
    period_number: int = Field(..., ge=1, le=12)
    year_number: int
    start_date: date
    end_date: date


class PeriodResponse(BaseModel):
    id: int
    period_number: int
    year_number: int
    start_date: date
    end_date: date
    is_open: bool
    is_current: bool
    gl_closed: bool
    sl_closed: bool
    pl_closed: bool
    stock_closed: bool

    class Config:
        from_attributes = True


@router.get("/periods")
def get_periods(
    year_number: Optional[int] = Query(None),
    is_open: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get company periods"""
    from app.models.system import CompanyPeriod
    from sqlalchemy import and_
    
    query = db.query(CompanyPeriod)
    
    filters = []
    if year_number:
        filters.append(CompanyPeriod.year_number == year_number)
    if is_open is not None:
        filters.append(CompanyPeriod.is_open == is_open)
    
    if filters:
        query = query.filter(and_(*filters))
    
    periods = query.order_by(CompanyPeriod.year_number.desc(), CompanyPeriod.period_number).all()
    return {"periods": periods}


@router.post("/periods", response_model=PeriodResponse)
def create_period(
    period_data: PeriodCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new company period"""
    from app.models.system import CompanyPeriod
    
    # Check for duplicate
    existing = db.query(CompanyPeriod).filter(
        CompanyPeriod.period_number == period_data.period_number,
        CompanyPeriod.year_number == period_data.year_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Period {period_data.period_number}/{period_data.year_number} already exists"
        )
    
    period = CompanyPeriod(
        **period_data.dict(),
        is_open=True,
        is_current=False,
        created_by=str(current_user_id)
    )
    
    db.add(period)
    db.commit()
    db.refresh(period)
    
    return period


@router.get("/periods/current")
def get_current_period(db: Session = Depends(get_db)):
    """Get current period"""
    from app.models.system import CompanyPeriod
    
    period = db.query(CompanyPeriod).filter(
        CompanyPeriod.is_current == True
    ).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current period found"
        )
    
    return period


@router.post("/periods/{period_id}/close")
def close_period(
    period_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Close accounting period"""
    service = PeriodEndService(db)
    period = service.close_period(period_id, current_user_id)
    return {"message": "Period closed successfully", "period": period}


@router.post("/periods/year-end/{year_number}")
def process_year_end(
    year_number: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Process year-end closing"""
    service = PeriodEndService(db)
    result = service.process_year_end(year_number, current_user_id)
    return result


@router.get("/periods/{period_id}/validate-close")
def validate_period_close(
    period_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Validate period can be closed"""
    service = PeriodEndService(db)
    validation = service.validate_period_close(period_id, current_user_id)
    return validation


@router.get("/config")
def get_system_config(db: Session = Depends(get_db)):
    """Get system configuration"""
    from app.models.system import SystemConfig
    
    config = db.query(SystemConfig).first()
    if not config:
        # Create default config
        config = SystemConfig(
            company_name="Applewood Computers",
            fiscal_year_start=1,
            base_currency="USD",
            decimal_places=2,
            vat_registration="123456789"
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    
    return config


@router.put("/config")
def update_system_config(
    company_name: Optional[str] = Query(None),
    fiscal_year_start: Optional[int] = Query(None, ge=1, le=12),
    base_currency: Optional[str] = Query(None),
    decimal_places: Optional[int] = Query(None, ge=0, le=4),
    vat_registration: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Update system configuration"""
    from app.models.system import SystemConfig
    from datetime import datetime
    
    config = db.query(SystemConfig).first()
    if not config:
        raise HTTPException(status_code=404, detail="System config not found")
    
    # Update fields
    if company_name:
        config.company_name = company_name
    if fiscal_year_start:
        config.fiscal_year_start = fiscal_year_start
    if base_currency:
        config.base_currency = base_currency
    if decimal_places is not None:
        config.decimal_places = decimal_places
    if vat_registration:
        config.vat_registration = vat_registration
    
    config.updated_at = datetime.now()
    config.updated_by = str(current_user_id)
    
    db.commit()
    db.refresh(config)
    
    return {"message": "System configuration updated", "config": config}


@router.get("/number-sequences")
def get_number_sequences(
    sequence_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get number sequences"""
    from app.models.control_tables import NumberSequence
    
    query = db.query(NumberSequence)
    
    if sequence_type:
        query = query.filter(NumberSequence.sequence_type == sequence_type)
    
    sequences = query.order_by(NumberSequence.sequence_type).all()
    return {"sequences": sequences}


@router.post("/number-sequences")
def create_number_sequence(
    sequence_type: str = Query(...),
    prefix: str = Query(...),
    current_number: int = Query(1, ge=1),
    min_digits: int = Query(6, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """Create number sequence"""
    from app.models.control_tables import NumberSequence
    
    # Check for duplicate
    existing = db.query(NumberSequence).filter(
        NumberSequence.sequence_type == sequence_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Number sequence {sequence_type} already exists"
        )
    
    sequence = NumberSequence(
        sequence_type=sequence_type,
        prefix=prefix,
        current_number=current_number,
        min_digits=min_digits
    )
    
    db.add(sequence)
    db.commit()
    db.refresh(sequence)
    
    return {"message": "Number sequence created", "sequence": sequence}


@router.get("/audit-trail")
def get_audit_trail(
    table_name: Optional[str] = Query(None),
    operation: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get audit trail"""
    from app.models.system import AuditTrail
    from sqlalchemy import and_
    
    query = db.query(AuditTrail)
    
    filters = []
    if table_name:
        filters.append(AuditTrail.table_name == table_name)
    if operation:
        filters.append(AuditTrail.operation == operation)
    if user_id:
        filters.append(AuditTrail.user_id == user_id)
    if from_date:
        filters.append(AuditTrail.created_at >= from_date)
    if to_date:
        filters.append(AuditTrail.created_at <= to_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    total_count = query.count()
    
    # Apply pagination
    audit_entries = query.order_by(AuditTrail.created_at.desc())\
                         .offset((page - 1) * page_size)\
                         .limit(page_size)\
                         .all()
    
    return {
        "audit_entries": audit_entries,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


@router.get("/database-info")
def get_database_info(db: Session = Depends(get_db)):
    """Get database information"""
    from sqlalchemy import text
    
    try:
        # Get database version
        version_result = db.execute(text("SELECT version()")).scalar()
        
        # Get table count
        table_count_result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)).scalar()
        
        return {
            "database_version": version_result,
            "table_count": table_count_result,
            "status": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/dashboard-stats", response_model=Dict[str, Any])
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """
    Get dashboard statistics
    
    Returns real-time statistics from the database to replace frontend mock data
    """
    try:
        # Import models - using imports here to avoid circular dependencies
        from app.models.purchase_transactions import PurchaseOrder
        from app.models.stock import StockItem, StockMovement
        from app.models.suppliers import Supplier
        from app.models.system import CompanyPeriod
        from app.models.general_ledger import JournalEntry
        from app.models.transactions import SalesInvoice, SalesOrder
        from app.models.customers import Customer
        
        # Calculate statistics
        stats = {}
        
        # Purchase Orders
        total_purchase_orders = db.query(func.count(PurchaseOrder.id)).scalar() or 0
        pending_approvals = db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.order_status == "PENDING"
        ).scalar() or 0
        
        # Stock Items
        total_stock_items = db.query(func.count(StockItem.id)).scalar() or 0
        low_stock_items = db.query(func.count(StockItem.id)).filter(
            and_(
                StockItem.quantity_on_hand <= StockItem.reorder_level,
                StockItem.is_stocked == True
            )
        ).scalar() or 0
        
        # Suppliers
        total_suppliers = db.query(func.count(Supplier.id)).scalar() or 0
        active_suppliers = db.query(func.count(Supplier.id)).filter(
            Supplier.is_active == True
        ).scalar() or 0
        
        # Periods
        open_periods = db.query(func.count(CompanyPeriod.id)).filter(
            CompanyPeriod.is_open == True
        ).scalar() or 0
        
        # Journal Entries
        total_journal_entries = db.query(func.count(JournalEntry.id)).scalar() or 0
        
        # Sales
        total_sales_orders = db.query(func.count(SalesOrder.id)).scalar() or 0
        total_sales_invoices = db.query(func.count(SalesInvoice.id)).scalar() or 0
        outstanding_invoices = db.query(func.count(SalesInvoice.id)).filter(
            SalesInvoice.is_paid == False
        ).scalar() or 0
        
        # Customers
        total_customers = db.query(func.count(Customer.id)).scalar() or 0
        
        # Recent Activity (last 7 days)
        recent_date = datetime.now() - timedelta(days=7)
        
        recent_orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.order_date >= recent_date
        ).order_by(PurchaseOrder.order_date.desc()).limit(5).all()
        
        recent_invoices = db.query(SalesInvoice).filter(
            SalesInvoice.invoice_date >= recent_date
        ).order_by(SalesInvoice.invoice_date.desc()).limit(5).all()
        
        recent_journal_entries = db.query(JournalEntry).filter(
            JournalEntry.journal_date >= recent_date
        ).order_by(JournalEntry.journal_date.desc()).limit(3).all()
        
        # Build activity list
        recent_activity = []
        
        # Add recent purchase orders
        for order in recent_orders:
            recent_activity.append({
                "id": f"po_{order.id}",
                "type": "purchase_order",
                "description": f"Purchase Order {order.order_number} created",
                "timestamp": order.order_date.isoformat() if order.order_date else None,
                "status": order.order_status.lower() if order.order_status else "unknown"
            })
        
        # Add recent invoices
        for invoice in recent_invoices:
            recent_activity.append({
                "id": f"inv_{invoice.id}",
                "type": "sales_invoice", 
                "description": f"Sales Invoice {invoice.invoice_number} created",
                "timestamp": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
                "status": "paid" if invoice.is_paid else "pending"
            })
        
        # Add recent journal entries
        for je in recent_journal_entries:
            recent_activity.append({
                "id": f"je_{je.id}",
                "type": "journal_entry",
                "description": f"Journal Entry {je.journal_number} posted",
                "timestamp": je.journal_date.isoformat() if je.journal_date else None,
                "status": "posted" if je.is_posted else "draft"
            })
        
        # Sort activity by timestamp (most recent first)
        recent_activity.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        recent_activity = recent_activity[:10]  # Limit to 10 items
        
        return {
            "stats": {
                "totalPurchaseOrders": total_purchase_orders,
                "pendingApprovals": pending_approvals,
                "stockItems": total_stock_items,
                "lowStockItems": low_stock_items,
                "totalSuppliers": total_suppliers,
                "activeSuppliers": active_suppliers,
                "openPeriods": open_periods,
                "journalEntries": total_journal_entries,
                "totalSalesOrders": total_sales_orders,
                "totalSalesInvoices": total_sales_invoices,
                "outstandingInvoices": outstanding_invoices,
                "totalCustomers": total_customers
            },
            "recentActivity": recent_activity,
            "generatedAt": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating dashboard statistics: {str(e)}"
        )