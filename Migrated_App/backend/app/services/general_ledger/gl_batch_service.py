"""
GL Batch Service
Migrated from COBOL gl080.cbl, gl090.cbl, gl095.cbl
Handles batch journal processing and control
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.general_ledger import (
    GLBatch, JournalHeader, JournalType, PostingStatus
)
from app.models.system import CompanyPeriod
from app.models.control_tables import NumberSequence
from app.services.base import BaseService
from app.services.general_ledger.journal_entry_service import JournalEntryService


class GLBatchService(BaseService):
    """GL batch processing service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.journal_service = JournalEntryService(db)
    
    def create_batch(
        self,
        batch_type: str,
        description: str,
        source_module: Optional[str] = None,
        control_count: Optional[int] = None,
        control_debits: Optional[Decimal] = None,
        control_credits: Optional[Decimal] = None,
        user_id: int = None
    ) -> GLBatch:
        """
        Create GL batch
        Migrated from gl080.cbl CREATE-BATCH
        """
        try:
            # Get current period
            period = self._get_current_period()
            if not period:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No current period found"
                )
            
            # Generate batch number
            batch_number = self._get_next_batch_number()
            
            # Create batch
            batch = GLBatch(
                batch_number=batch_number,
                batch_date=datetime.now(),
                batch_type=batch_type,
                description=description,
                source_module=source_module,
                period_id=period.id,
                control_count=control_count or 0,
                control_debits=control_debits or Decimal("0"),
                control_credits=control_credits or Decimal("0"),
                actual_count=0,
                actual_debits=Decimal("0"),
                actual_credits=Decimal("0"),
                is_balanced=False,
                is_posted=False,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(batch)
            self.db.commit()
            self.db.refresh(batch)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="gl_batches",
                record_id=str(batch.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created GL batch {batch_number}"
            )
            
            return batch
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating batch: {str(e)}"
            )
    
    def add_journal_to_batch(
        self,
        batch_id: int,
        journal_data: Dict,
        user_id: int
    ) -> JournalHeader:
        """
        Add journal to batch
        Migrated from gl090.cbl ADD-TO-BATCH
        """
        try:
            # Get batch
            batch = self.db.query(GLBatch).filter(
                GLBatch.id == batch_id
            ).first()
            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Batch not found"
                )
            
            if batch.is_posted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot add to posted batch"
                )
            
            # Create journal with batch reference
            journal = self.journal_service.create_journal_entry(
                journal_date=journal_data["journal_date"],
                journal_type=journal_data["journal_type"],
                description=journal_data["description"],
                reference=journal_data.get("reference"),
                journal_lines=journal_data["journal_lines"],
                source_module=batch.source_module,
                source_reference=journal_data.get("source_reference"),
                auto_post=False,  # Don't auto-post batch journals
                user_id=user_id
            )
            
            # Link journal to batch
            journal.batch_id = batch.id
            
            # Update batch actuals
            batch.actual_count += 1
            batch.actual_debits += journal.total_debits
            batch.actual_credits += journal.total_credits
            
            # Check if batch is balanced
            self._check_batch_balance(batch)
            
            self.db.commit()
            self.db.refresh(journal)
            
            return journal
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding journal to batch: {str(e)}"
            )
    
    def validate_batch(
        self,
        batch_id: int,
        user_id: int
    ) -> Dict:
        """
        Validate batch before posting
        Migrated from gl095.cbl VALIDATE-BATCH
        """
        try:
            # Get batch
            batch = self.db.query(GLBatch).filter(
                GLBatch.id == batch_id
            ).first()
            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Batch not found"
                )
            
            validation_errors = []
            
            # Check control totals
            if batch.control_count > 0:
                if batch.actual_count != batch.control_count:
                    validation_errors.append({
                        "type": "COUNT_MISMATCH",
                        "message": f"Expected {batch.control_count} journals, found {batch.actual_count}"
                    })
            
            if batch.control_debits > 0:
                if batch.actual_debits != batch.control_debits:
                    validation_errors.append({
                        "type": "DEBIT_MISMATCH",
                        "message": f"Expected debits {batch.control_debits}, found {batch.actual_debits}"
                    })
            
            if batch.control_credits > 0:
                if batch.actual_credits != batch.control_credits:
                    validation_errors.append({
                        "type": "CREDIT_MISMATCH",
                        "message": f"Expected credits {batch.control_credits}, found {batch.actual_credits}"
                    })
            
            # Check if balanced
            if batch.actual_debits != batch.actual_credits:
                validation_errors.append({
                    "type": "NOT_BALANCED",
                    "message": f"Batch not balanced. Debits: {batch.actual_debits}, Credits: {batch.actual_credits}"
                })
            
            # Check individual journals
            for journal in batch.journals:
                if journal.posting_status == PostingStatus.POSTED:
                    validation_errors.append({
                        "type": "ALREADY_POSTED",
                        "message": f"Journal {journal.journal_number} already posted"
                    })
                
                if journal.total_debits != journal.total_credits:
                    validation_errors.append({
                        "type": "JOURNAL_NOT_BALANCED",
                        "message": f"Journal {journal.journal_number} not balanced"
                    })
            
            # Update batch validation status
            if not validation_errors:
                batch.is_balanced = True
                batch.validation_errors = None
            else:
                batch.is_balanced = False
                batch.validation_errors = "\n".join(
                    [f"{e['type']}: {e['message']}" for e in validation_errors]
                )
            
            batch.updated_at = datetime.now()
            batch.updated_by = str(user_id)
            
            self.db.commit()
            
            return {
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "is_valid": len(validation_errors) == 0,
                "validation_errors": validation_errors,
                "summary": {
                    "journal_count": batch.actual_count,
                    "total_debits": batch.actual_debits,
                    "total_credits": batch.actual_credits,
                    "is_balanced": batch.is_balanced
                }
            }
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error validating batch: {str(e)}"
            )
    
    def post_batch(
        self,
        batch_id: int,
        user_id: int
    ) -> GLBatch:
        """
        Post entire batch
        Migrated from gl095.cbl POST-BATCH
        """
        try:
            # Get batch
            batch = self.db.query(GLBatch).filter(
                GLBatch.id == batch_id
            ).first()
            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Batch not found"
                )
            
            if batch.is_posted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Batch already posted"
                )
            
            if not batch.is_balanced:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Batch is not balanced"
                )
            
            # Validate batch first
            validation = self.validate_batch(batch_id, user_id)
            if not validation["is_valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Batch validation failed",
                    errors=validation["validation_errors"]
                )
            
            # Post all journals in batch
            posted_count = 0
            for journal in batch.journals:
                if journal.posting_status == PostingStatus.DRAFT:
                    self.journal_service.post_journal(journal.id, user_id)
                    posted_count += 1
            
            # Update batch status
            batch.is_posted = True
            batch.posted_date = datetime.now()
            batch.posted_by = str(user_id)
            
            self.db.commit()
            self.db.refresh(batch)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="gl_batches",
                record_id=str(batch.id),
                operation="POST",
                user_id=user_id,
                details=f"Posted batch {batch.batch_number} with {posted_count} journals"
            )
            
            return batch
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error posting batch: {str(e)}"
            )
    
    def import_batch_from_file(
        self,
        file_content: str,
        file_format: str,  # CSV, TXT, XML
        user_id: int
    ) -> GLBatch:
        """
        Import batch from file
        Migrated from gl090.cbl IMPORT-BATCH
        """
        try:
            # Parse file based on format
            if file_format == "CSV":
                journals = self._parse_csv_batch(file_content)
            elif file_format == "TXT":
                journals = self._parse_text_batch(file_content)
            elif file_format == "XML":
                journals = self._parse_xml_batch(file_content)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file format: {file_format}"
                )
            
            # Calculate control totals
            control_count = len(journals)
            control_debits = sum(
                sum(Decimal(str(l.get("debit_amount", "0"))) 
                    for l in j["lines"])
                for j in journals
            )
            control_credits = sum(
                sum(Decimal(str(l.get("credit_amount", "0"))) 
                    for l in j["lines"])
                for j in journals
            )
            
            # Create batch
            batch = self.create_batch(
                batch_type="IMPORT",
                description=f"Imported from {file_format} file",
                source_module="IMPORT",
                control_count=control_count,
                control_debits=control_debits,
                control_credits=control_credits,
                user_id=user_id
            )
            
            # Add journals to batch
            for journal_data in journals:
                self.add_journal_to_batch(
                    batch_id=batch.id,
                    journal_data={
                        "journal_date": journal_data["date"],
                        "journal_type": JournalType.MANUAL,
                        "description": journal_data["description"],
                        "reference": journal_data.get("reference"),
                        "journal_lines": journal_data["lines"]
                    },
                    user_id=user_id
                )
            
            return batch
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error importing batch: {str(e)}"
            )
    
    def get_batches(
        self,
        period_id: Optional[int] = None,
        batch_type: Optional[str] = None,
        is_posted: Optional[bool] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Get batches with filtering
        Migrated from gl095.cbl LIST-BATCHES
        """
        try:
            query = self.db.query(GLBatch)
            
            # Apply filters
            if period_id:
                query = query.filter(GLBatch.period_id == period_id)
            
            if batch_type:
                query = query.filter(GLBatch.batch_type == batch_type)
            
            if is_posted is not None:
                query = query.filter(GLBatch.is_posted == is_posted)
            
            if from_date:
                query = query.filter(GLBatch.batch_date >= from_date)
            
            if to_date:
                query = query.filter(GLBatch.batch_date <= to_date)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            batches = query.order_by(GLBatch.batch_date.desc(),
                                   GLBatch.batch_number.desc())\
                         .offset((page - 1) * page_size)\
                         .limit(page_size)\
                         .all()
            
            return {
                "batches": batches,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving batches: {str(e)}"
            )
    
    def _get_next_batch_number(self) -> str:
        """Generate next batch number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "GL_BATCH"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="GL_BATCH",
                prefix="BAT",
                current_number=1,
                min_digits=6
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        batch_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return batch_number
    
    def _check_batch_balance(self, batch: GLBatch):
        """Check if batch is balanced"""
        batch.is_balanced = (
            batch.actual_debits == batch.actual_credits and
            (batch.control_count == 0 or batch.actual_count == batch.control_count) and
            (batch.control_debits == 0 or batch.actual_debits == batch.control_debits) and
            (batch.control_credits == 0 or batch.actual_credits == batch.control_credits)
        )
    
    def _parse_csv_batch(self, content: str) -> List[Dict]:
        """Parse CSV batch file"""
        import csv
        import io
        
        journals = []
        current_journal = None
        
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            if row.get("type") == "HEADER":
                if current_journal:
                    journals.append(current_journal)
                
                current_journal = {
                    "date": datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    "description": row["description"],
                    "reference": row.get("reference"),
                    "lines": []
                }
            
            elif row.get("type") == "LINE" and current_journal:
                current_journal["lines"].append({
                    "account_code": row["account_code"],
                    "debit_amount": row.get("debit_amount", "0"),
                    "credit_amount": row.get("credit_amount", "0"),
                    "description": row.get("description", ""),
                    "reference": row.get("reference", "")
                })
        
        if current_journal:
            journals.append(current_journal)
        
        return journals
    
    def _parse_text_batch(self, content: str) -> List[Dict]:
        """Parse text batch file - simplified example"""
        # Would implement specific text format parsing
        return []
    
    def _parse_xml_batch(self, content: str) -> List[Dict]:
        """Parse XML batch file - simplified example"""
        # Would implement XML parsing
        return []