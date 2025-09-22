"""
Goods Receipt Service
Migrated from COBOL pl100.cbl, pl110.cbl, pl115.cbl
Handles goods receipt processing and stock updates
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from fastapi import HTTPException, status

from app.models.purchase_transactions import (
    GoodsReceipt, GoodsReceiptLine, GoodsReceiptStatus,
    PurchaseOrder, PurchaseOrderLine
)
from app.models.suppliers import Supplier
from app.models.stock import StockItem, StockMovement
from app.models.control_tables import NumberSequence
from app.models.system import AuditTrail
from app.services.base import BaseService
from app.services.stock_service import StockService


class GoodsReceiptService(BaseService):
    """Goods receipt processing service"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.stock_service = StockService(db)
    
    def create_goods_receipt(
        self,
        purchase_order_id: Optional[int] = None,
        supplier_code: Optional[str] = None,
        delivery_note: Optional[str] = None,
        receipt_lines: Optional[List[Dict]] = None,
        user_id: int = None
    ) -> GoodsReceipt:
        """
        Create goods receipt note
        Migrated from pl100.cbl CREATE-GOODS-RECEIPT
        """
        try:
            # Validate inputs
            if not purchase_order_id and not supplier_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either purchase order or supplier must be specified"
                )
            
            # Get supplier
            supplier = None
            purchase_order = None
            
            if purchase_order_id:
                purchase_order = self.db.query(PurchaseOrder).filter(
                    PurchaseOrder.id == purchase_order_id
                ).first()
                if not purchase_order:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Purchase order not found"
                    )
                supplier = purchase_order.supplier
            else:
                supplier = self.db.query(Supplier).filter(
                    Supplier.supplier_code == supplier_code
                ).first()
                if not supplier:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Supplier {supplier_code} not found"
                    )
            
            # Generate receipt number
            receipt_number = self._get_next_receipt_number()
            
            # Create receipt header
            receipt = GoodsReceipt(
                receipt_number=receipt_number,
                receipt_date=datetime.now(),
                purchase_order_id=purchase_order_id,
                supplier_id=supplier.id,
                delivery_note=delivery_note,
                received_by=str(user_id) if user_id else None,
                receipt_status=GoodsReceiptStatus.PENDING,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(receipt)
            self.db.flush()
            
            # Process receipt lines
            if purchase_order_id and not receipt_lines:
                # Create from PO lines
                receipt_lines = self._create_lines_from_po(purchase_order)
            
            line_number = 0
            total_quantity = Decimal("0")
            
            for line_data in receipt_lines:
                line_number += 10
                
                # Get stock item
                stock_item = None
                if line_data.get("stock_code"):
                    stock_item = self.db.query(StockItem).filter(
                        StockItem.stock_code == line_data["stock_code"]
                    ).first()
                
                # Create receipt line
                quantity_received = Decimal(str(line_data["quantity_received"]))
                
                receipt_line = GoodsReceiptLine(
                    receipt_id=receipt.id,
                    line_number=line_number,
                    po_line_id=line_data.get("po_line_id"),
                    stock_id=stock_item.id if stock_item else None,
                    stock_code=line_data.get("stock_code"),
                    description=line_data["description"],
                    quantity_ordered=Decimal(str(line_data.get("quantity_ordered", 0))),
                    quantity_received=quantity_received,
                    quantity_accepted=quantity_received,
                    quantity_rejected=Decimal("0"),
                    location_code=line_data.get("location_code"),
                    bin_number=line_data.get("bin_number"),
                    batch_number=line_data.get("batch_number"),
                    expiry_date=line_data.get("expiry_date")
                )
                
                receipt.receipt_lines.append(receipt_line)
                total_quantity += quantity_received
                
                # Update PO line if linked
                if line_data.get("po_line_id"):
                    self._update_po_line_receipt(
                        line_data["po_line_id"],
                        quantity_received
                    )
            
            # Update receipt totals
            receipt.total_lines = len(receipt_lines)
            receipt.total_quantity = total_quantity
            
            self.db.commit()
            self.db.refresh(receipt)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="goods_receipts",
                record_id=str(receipt.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created GRN {receipt_number}"
            )
            
            return receipt
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating goods receipt: {str(e)}"
            )
    
    def process_receipt_inspection(
        self,
        receipt_id: int,
        inspection_results: List[Dict],
        inspector_id: int
    ) -> GoodsReceipt:
        """
        Process receipt inspection results
        Migrated from pl110.cbl INSPECT-GOODS
        """
        try:
            # Get receipt
            receipt = self.db.query(GoodsReceipt).filter(
                GoodsReceipt.id == receipt_id
            ).first()
            if not receipt:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Goods receipt not found"
                )
            
            if receipt.receipt_status != GoodsReceiptStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot inspect {receipt.receipt_status.value} receipt"
                )
            
            # Process inspection results
            total_rejected = Decimal("0")
            
            for result in inspection_results:
                line = next(
                    (l for l in receipt.receipt_lines if l.line_number == result["line_number"]),
                    None
                )
                if not line:
                    continue
                
                # Update quantities
                quantity_accepted = Decimal(str(result.get("quantity_accepted", line.quantity_received)))
                quantity_rejected = Decimal(str(result.get("quantity_rejected", "0")))
                
                if quantity_accepted + quantity_rejected != line.quantity_received:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Accepted + rejected quantities must equal received quantity for line {line.line_number}"
                    )
                
                line.quantity_accepted = quantity_accepted
                line.quantity_rejected = quantity_rejected
                line.inspection_result = result.get("inspection_result", "PASS" if quantity_rejected == 0 else "PARTIAL")
                line.rejection_reason = result.get("rejection_reason")
                
                total_rejected += quantity_rejected
            
            # Update receipt status
            receipt.inspection_date = datetime.now()
            receipt.inspected_by = str(inspector_id)
            
            if total_rejected == receipt.total_quantity:
                receipt.receipt_status = GoodsReceiptStatus.REJECTED
                receipt.rejection_reason = "All items rejected"
            else:
                receipt.receipt_status = GoodsReceiptStatus.INSPECTED
            
            self.db.commit()
            self.db.refresh(receipt)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="goods_receipts",
                record_id=str(receipt.id),
                operation="INSPECT",
                user_id=inspector_id,
                details=f"Inspected GRN {receipt.receipt_number}"
            )
            
            return receipt
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing inspection: {str(e)}"
            )
    
    def post_receipt_to_stock(
        self,
        receipt_id: int,
        user_id: int
    ) -> GoodsReceipt:
        """
        Post receipt to stock
        Migrated from pl115.cbl POST-TO-STOCK
        """
        try:
            # Get receipt
            receipt = self.db.query(GoodsReceipt).filter(
                GoodsReceipt.id == receipt_id
            ).first()
            if not receipt:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Goods receipt not found"
                )
            
            if receipt.receipt_status not in [GoodsReceiptStatus.RECEIVED, GoodsReceiptStatus.INSPECTED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot post {receipt.receipt_status.value} receipt to stock"
                )
            
            if receipt.posted_to_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Receipt already posted to stock"
                )
            
            # Process each line
            for line in receipt.receipt_lines:
                if line.stock_id and line.quantity_accepted > 0:
                    # Create stock movement
                    movement = self.stock_service.create_stock_movement(
                        stock_id=line.stock_id,
                        movement_type="GOODS_RECEIPT",
                        quantity=line.quantity_accepted,
                        reference_type="GOODS_RECEIPT",
                        reference_number=receipt.receipt_number,
                        location_code=line.location_code,
                        batch_number=line.batch_number,
                        cost_price=self._get_line_cost_price(line),
                        user_id=user_id
                    )
            
            # Update receipt
            receipt.posted_to_stock = True
            receipt.stock_posting_date = datetime.now()
            receipt.receipt_status = GoodsReceiptStatus.POSTED
            
            self.db.commit()
            self.db.refresh(receipt)
            
            # Check if PO is complete
            if receipt.purchase_order_id:
                from app.services.purchase_ledger.purchase_order_service import PurchaseOrderService
                po_service = PurchaseOrderService(self.db)
                po_service.check_order_completion(receipt.purchase_order_id)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="goods_receipts",
                record_id=str(receipt.id),
                operation="POST",
                user_id=user_id,
                details=f"Posted GRN {receipt.receipt_number} to stock"
            )
            
            return receipt
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error posting to stock: {str(e)}"
            )
    
    def get_pending_receipts(
        self,
        supplier_code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[GoodsReceipt]:
        """
        Get pending goods receipts
        Migrated from pl115.cbl LIST-PENDING-RECEIPTS
        """
        try:
            query = self.db.query(GoodsReceipt).filter(
                GoodsReceipt.receipt_status.in_([
                    GoodsReceiptStatus.PENDING,
                    GoodsReceiptStatus.RECEIVED,
                    GoodsReceiptStatus.INSPECTED
                ])
            )
            
            if supplier_code:
                query = query.join(Supplier).filter(
                    Supplier.supplier_code == supplier_code
                )
            
            if from_date:
                query = query.filter(GoodsReceipt.receipt_date >= from_date)
            
            if to_date:
                query = query.filter(GoodsReceipt.receipt_date <= to_date)
            
            return query.order_by(GoodsReceipt.receipt_date).all()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pending receipts: {str(e)}"
            )
    
    def _get_next_receipt_number(self) -> str:
        """Generate next goods receipt number"""
        sequence = self.db.query(NumberSequence).filter(
            NumberSequence.sequence_type == "GOODS_RECEIPT"
        ).with_for_update().first()
        
        if not sequence:
            sequence = NumberSequence(
                sequence_type="GOODS_RECEIPT",
                prefix="GRN",
                current_number=1,
                min_digits=6
            )
            self.db.add(sequence)
        
        sequence.current_number += 1
        number_str = str(sequence.current_number).zfill(sequence.min_digits)
        receipt_number = f"{sequence.prefix}{number_str}"
        
        self.db.commit()
        return receipt_number
    
    def _create_lines_from_po(self, purchase_order: PurchaseOrder) -> List[Dict]:
        """Create receipt lines from PO lines with outstanding quantities"""
        lines = []
        
        for po_line in purchase_order.order_lines:
            if po_line.quantity_outstanding > 0:
                lines.append({
                    "po_line_id": po_line.id,
                    "stock_code": po_line.stock_code,
                    "description": po_line.description,
                    "quantity_ordered": po_line.quantity_ordered,
                    "quantity_received": po_line.quantity_outstanding
                })
        
        return lines
    
    def _update_po_line_receipt(self, po_line_id: int, quantity_received: Decimal):
        """Update PO line with received quantity"""
        po_line = self.db.query(PurchaseOrderLine).filter(
            PurchaseOrderLine.id == po_line_id
        ).first()
        
        if po_line:
            po_line.quantity_received += quantity_received
            po_line.quantity_outstanding = po_line.quantity_ordered - po_line.quantity_received
            
            if po_line.quantity_outstanding <= 0:
                po_line.line_status = "COMPLETE"
            else:
                po_line.line_status = "PARTIAL"
            
            po_line.updated_at = datetime.now()
    
    def _get_line_cost_price(self, receipt_line: GoodsReceiptLine) -> Decimal:
        """Get cost price for stock posting"""
        # If linked to PO, use PO price
        if receipt_line.po_line_id:
            po_line = self.db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.id == receipt_line.po_line_id
            ).first()
            if po_line:
                return po_line.unit_price
        
        # Otherwise, get from stock item
        if receipt_line.stock_id:
            stock_item = self.db.query(StockItem).filter(
                StockItem.id == receipt_line.stock_id
            ).first()
            if stock_item:
                return stock_item.unit_cost or Decimal("0")
        
        return Decimal("0")