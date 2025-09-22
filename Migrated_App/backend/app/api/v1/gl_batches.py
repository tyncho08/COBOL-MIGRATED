"""
GL Batches API Router
REST endpoints for GL batch processing
"""
from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.general_ledger.gl_batch_service import GLBatchService
from app.models.general_ledger import JournalType

router = APIRouter(prefix="/gl-batches", tags=["GL Batches"])


# Pydantic models
class GLBatchCreate(BaseModel):
    batch_type: str
    description: str
    source_module: Optional[str] = None
    control_count: Optional[int] = None
    control_debits: Optional[Decimal] = None
    control_credits: Optional[Decimal] = None


class JournalToBatchCreate(BaseModel):
    journal_date: date
    journal_type: JournalType
    description: str
    reference: Optional[str] = None
    journal_lines: List[dict]
    source_reference: Optional[str] = None


class GLBatchResponse(BaseModel):
    id: int
    batch_number: str
    batch_date: date
    batch_type: str
    description: str
    source_module: Optional[str]
    control_count: int
    control_debits: Decimal
    control_credits: Decimal
    actual_count: int
    actual_debits: Decimal
    actual_credits: Decimal
    is_balanced: bool
    is_posted: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=GLBatchResponse)
def create_batch(
    batch_data: GLBatchCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Create new GL batch"""
    service = GLBatchService(db)
    batch = service.create_batch(
        **batch_data.dict(),
        user_id=current_user_id
    )
    return batch


@router.get("/{batch_id}", response_model=GLBatchResponse)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """Get GL batch by ID"""
    from app.models.general_ledger import GLBatch
    batch = db.query(GLBatch).filter(GLBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    return batch


@router.post("/{batch_id}/journals")
def add_journal_to_batch(
    batch_id: int,
    journal_data: JournalToBatchCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Add journal to batch"""
    service = GLBatchService(db)
    journal = service.add_journal_to_batch(
        batch_id=batch_id,
        journal_data=journal_data.dict(),
        user_id=current_user_id
    )
    return {"message": "Journal added to batch", "journal_id": journal.id}


@router.post("/{batch_id}/validate")
def validate_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Validate batch before posting"""
    service = GLBatchService(db)
    validation = service.validate_batch(batch_id, current_user_id)
    return validation


@router.post("/{batch_id}/post")
def post_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Post entire batch"""
    service = GLBatchService(db)
    batch = service.post_batch(batch_id, current_user_id)
    return {"message": "Batch posted successfully", "batch_number": batch.batch_number}


@router.post("/import")
async def import_batch_from_file(
    file: UploadFile = File(...),
    file_format: str = Query(..., regex="^(CSV|TXT|XML)$"),
    db: Session = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Import batch from file"""
    # Read file content
    content = await file.read()
    file_content = content.decode('utf-8')
    
    service = GLBatchService(db)
    batch = service.import_batch_from_file(
        file_content=file_content,
        file_format=file_format,
        user_id=current_user_id
    )
    return {"message": "Batch imported successfully", "batch_id": batch.id}


@router.get("/")
def search_batches(
    period_id: Optional[int] = Query(None),
    batch_type: Optional[str] = Query(None),
    is_posted: Optional[bool] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search GL batches"""
    service = GLBatchService(db)
    result = service.get_batches(
        period_id=period_id,
        batch_type=batch_type,
        is_posted=is_posted,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return result


@router.get("/{batch_id}/journals")
def get_batch_journals(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """Get journals in batch"""
    from app.models.general_ledger import JournalHeader
    journals = db.query(JournalHeader).filter(JournalHeader.batch_id == batch_id).all()
    return {"journals": journals}


@router.get("/{batch_id}/summary")
def get_batch_summary(
    batch_id: int,
    db: Session = Depends(get_db)
):
    """Get batch summary with validation status"""
    service = GLBatchService(db)
    validation = service.validate_batch(batch_id, user_id=1)
    return validation