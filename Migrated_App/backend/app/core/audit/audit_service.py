"""
Audit Trail Service
Implements comprehensive audit logging as per ACAS requirements
"""
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models import AuditTrail


class AuditService:
    """
    Comprehensive audit trail service matching ACAS audit requirements
    Tracks all changes to business data with before/after images
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_audit_entry(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        user_id: int,
        before_data: Optional[Dict[str, Any]] = None,
        after_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        application_version: str = "1.0.0"
    ) -> AuditTrail:
        """
        Create an audit trail entry
        
        Args:
            table_name: Name of the table being audited
            record_id: ID of the record being changed
            operation: INSERT, UPDATE, DELETE
            user_id: ID of the user making the change
            before_data: Record state before change (for UPDATE/DELETE)
            after_data: Record state after change (for INSERT/UPDATE)
            session_id: Optional session identifier
            ip_address: Optional user IP address
            user_agent: Optional browser/client info
            application_version: Version of the application
            
        Returns:
            Created audit trail entry
        """
        # Calculate changed fields for UPDATE operations
        changed_fields = None
        if operation == "UPDATE" and before_data and after_data:
            changed_fields = self._calculate_changed_fields(before_data, after_data)
        
        # Create audit entry
        audit_entry = AuditTrail(
            table_name=table_name,
            record_id=str(record_id),
            operation_type=operation,
            user_id=user_id,
            before_image=before_data,
            after_image=after_data,
            changed_fields=changed_fields,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            application_version=application_version
        )
        
        self.db.add(audit_entry)
        # Note: Don't commit here - let the calling transaction handle it
        
        return audit_entry
    
    def _calculate_changed_fields(
        self,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate which fields changed and their before/after values
        """
        changed = {}
        
        # Check all fields in after_data
        for field, after_value in after_data.items():
            before_value = before_data.get(field)
            
            # Convert to comparable format
            if isinstance(after_value, (datetime, date)):
                after_value = after_value.isoformat() if after_value else None
            if isinstance(before_value, (datetime, date)):
                before_value = before_value.isoformat() if before_value else None
            
            # Check if changed
            if before_value != after_value:
                changed[field] = {
                    "before": before_value,
                    "after": after_value
                }
        
        # Check for deleted fields
        for field in before_data:
            if field not in after_data:
                changed[field] = {
                    "before": before_data[field],
                    "after": None
                }
        
        return changed
    
    def get_audit_trail(
        self,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        operation_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditTrail]:
        """
        Retrieve audit trail entries with filtering
        """
        query = self.db.query(AuditTrail)
        
        # Apply filters
        if table_name:
            query = query.filter(AuditTrail.table_name == table_name)
        if record_id:
            query = query.filter(AuditTrail.record_id == record_id)
        if user_id:
            query = query.filter(AuditTrail.user_id == user_id)
        if from_date:
            query = query.filter(AuditTrail.timestamp >= from_date)
        if to_date:
            query = query.filter(AuditTrail.timestamp <= to_date)
        if operation_type:
            query = query.filter(AuditTrail.operation_type == operation_type)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(AuditTrail.timestamp.desc())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_record_history(
        self,
        table_name: str,
        record_id: str
    ) -> List[AuditTrail]:
        """
        Get complete history of a specific record
        """
        return self.db.query(AuditTrail).filter(
            AuditTrail.table_name == table_name,
            AuditTrail.record_id == record_id
        ).order_by(AuditTrail.timestamp).all()
    
    def reconstruct_record_at_point(
        self,
        table_name: str,
        record_id: str,
        point_in_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Reconstruct a record's state at a specific point in time
        """
        # Get all audit entries up to the point in time
        audit_entries = self.db.query(AuditTrail).filter(
            AuditTrail.table_name == table_name,
            AuditTrail.record_id == record_id,
            AuditTrail.timestamp <= point_in_time
        ).order_by(AuditTrail.timestamp).all()
        
        if not audit_entries:
            return None
        
        # Start with the first INSERT
        record_state = None
        for entry in audit_entries:
            if entry.operation_type == "INSERT":
                record_state = entry.after_image.copy() if entry.after_image else {}
            elif entry.operation_type == "UPDATE" and record_state:
                # Apply updates
                if entry.after_image:
                    record_state.update(entry.after_image)
            elif entry.operation_type == "DELETE":
                # Record was deleted
                return None
        
        return record_state