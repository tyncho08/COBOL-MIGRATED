"""
Journal Entries API Router
REST endpoints for journal entry management
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.general_ledger.journal_entry_service import JournalEntryService
from app.models.general_ledger import JournalType, PostingStatus

router = APIRouter(prefix="/journal-entries", tags=["Journal Entries"])


# Pydantic models
class JournalLineCreate(BaseModel):
    account_code: str
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")
    description: Optional[str] = None
    reference: Optional[str] = None
    analysis_code1: Optional[str] = None
    analysis_code2: Optional[str] = None
    analysis_code3: Optional[str] = None
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1")


class JournalEntryCreate(BaseModel):
    journal_date: date
    journal_type: JournalType
    description: str
    reference: Optional[str] = None
    journal_lines: List[JournalLineCreate]
    source_module: Optional[str] = None
    source_reference: Optional[str] = None
    auto_post: bool = False


class RecurringJournalCreate(BaseModel):
    template_name: str
    journal_type: JournalType
    description: str
    journal_lines: List[JournalLineCreate]
    frequency: str = Field(..., regex="^(MONTHLY|QUARTERLY|YEARLY)$")
    next_date: date


class JournalEntryResponse(BaseModel):
    id: int
    journal_number: str
    journal_date: date
    journal_type: str
    description: str
    reference: Optional[str]
    posting_status: str
    total_debits: Decimal
    total_credits: Decimal
    line_count: int
    source_module: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model=JournalEntryResponse)
def create_journal_entry(
    journal_data: JournalEntryCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new journal entry"""
    service = JournalEntryService(db)
    journal = service.create_journal_entry(
        journal_date=journal_data.journal_date,
        journal_type=journal_data.journal_type,
        description=journal_data.description,
        reference=journal_data.reference,
        journal_lines=[line.dict() for line in journal_data.journal_lines],
        source_module=journal_data.source_module,
        source_reference=journal_data.source_reference,
        auto_post=journal_data.auto_post,
        user_id=current_user_id
    )
    return journal


@router.get("/{journal_id}", response_model=JournalEntryResponse)
def get_journal_entry(
    journal_id: int,
    include_lines: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get journal entry by ID"""
    from app.services.general_ledger.gl_inquiry_service import GLInquiryService
    service = GLInquiryService(db)
    journal = service.get_journal_inquiry(
        journal_id=journal_id,
        include_lines=include_lines
    )
    return journal["journal"]


@router.get("/by-number/{journal_number}")
def get_journal_by_number(
    journal_number: str,
    include_lines: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get journal entry by number"""
    from app.services.general_ledger.gl_inquiry_service import GLInquiryService
    service = GLInquiryService(db)
    journal = service.get_journal_inquiry(
        journal_number=journal_number,
        include_lines=include_lines
    )
    return journal


@router.post("/{journal_id}/post")
def post_journal_entry(
    journal_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Post journal entry to ledger"""
    service = JournalEntryService(db)
    journal = service.post_journal(journal_id, current_user_id)
    return {"message": "Journal posted successfully", "journal_number": journal.journal_number}


@router.post("/{journal_id}/reverse")
def reverse_journal_entry(
    journal_id: int,
    reversal_date: date = Query(...),
    reversal_reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Reverse posted journal entry"""
    service = JournalEntryService(db)
    reversal = service.reverse_journal(
        journal_id=journal_id,
        reversal_date=reversal_date,
        reversal_reason=reversal_reason,
        user_id=current_user_id
    )
    return {"message": "Journal reversed successfully", "reversal_number": reversal.journal_number}


@router.post("/recurring-templates")
def create_recurring_template(
    template_data: RecurringJournalCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create recurring journal template"""
    service = JournalEntryService(db)
    template = service.create_recurring_journal_template(
        template_name=template_data.template_name,
        journal_type=template_data.journal_type,
        description=template_data.description,
        journal_lines=[line.dict() for line in template_data.journal_lines],
        frequency=template_data.frequency,
        next_date=template_data.next_date,
        user_id=current_user_id
    )
    return {"message": "Recurring template created", "template": template}


@router.get("/")
def search_journal_entries(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    journal_type: Optional[JournalType] = Query(None),
    source_module: Optional[str] = Query(None),
    posting_status: Optional[PostingStatus] = Query(None),
    reference: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    amount_from: Optional[Decimal] = Query(None),
    amount_to: Optional[Decimal] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search journal entries"""
    from app.services.general_ledger.gl_inquiry_service import GLInquiryService
    service = GLInquiryService(db)
    result = service.search_journals(
        from_date=from_date,
        to_date=to_date,
        journal_type=journal_type.value if journal_type else None,
        source_module=source_module,
        posting_status=posting_status,
        reference=reference,
        description=description,
        amount_from=amount_from,
        amount_to=amount_to,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/{journal_id}/lines")
def get_journal_lines(
    journal_id: int,
    db: Session = Depends(get_db)
):
    """Get journal entry lines"""
    from app.services.general_ledger.gl_inquiry_service import GLInquiryService
    service = GLInquiryService(db)
    journal = service.get_journal_inquiry(journal_id=journal_id, include_lines=True)
    return {"lines": journal["lines"]}


@router.get("/period/{period_id}")
def get_journals_for_period(
    period_id: int,
    posting_status: Optional[PostingStatus] = Query(None),
    journal_type: Optional[JournalType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get journals for specific period"""
    service = JournalEntryService(db)
    result = service.get_journal_entries(
        period_id=period_id,
        journal_type=journal_type,
        posting_status=posting_status,
        page=page,
        page_size=page_size
    )
    return result