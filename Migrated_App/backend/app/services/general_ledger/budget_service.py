"""
Budget Service
Migrated from COBOL gl200.cbl, gl210.cbl, gl220.cbl
Handles budget management and variance analysis
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status

from app.models.general_ledger import (
    BudgetHeader, BudgetLine, ChartOfAccounts, AccountBalance
)
from app.models.system import CompanyPeriod
from app.services.base import BaseService


class BudgetService(BaseService):
    """Budget management service"""
    
    def create_budget(
        self,
        budget_name: str,
        fiscal_year: int,
        budget_type: str = "ANNUAL",
        description: Optional[str] = None,
        user_id: int = None
    ) -> BudgetHeader:
        """
        Create budget header
        Migrated from gl200.cbl CREATE-BUDGET
        """
        try:
            # Check for duplicate
            existing = self.db.query(BudgetHeader).filter(
                and_(
                    BudgetHeader.budget_name == budget_name,
                    BudgetHeader.fiscal_year == fiscal_year
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Budget '{budget_name}' already exists for year {fiscal_year}"
                )
            
            # Create budget header
            budget = BudgetHeader(
                budget_name=budget_name,
                fiscal_year=fiscal_year,
                budget_type=budget_type,
                description=description,
                is_active=True,
                is_approved=False,
                total_amount=Decimal("0"),
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(budget)
            self.db.commit()
            self.db.refresh(budget)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="budget_headers",
                record_id=str(budget.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Created budget {budget_name} for year {fiscal_year}"
            )
            
            return budget
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating budget: {str(e)}"
            )
    
    def add_budget_line(
        self,
        budget_id: int,
        account_code: str,
        annual_amount: Decimal,
        spread_method: str = "EVEN",
        period_amounts: Optional[List[Decimal]] = None,
        notes: Optional[str] = None,
        user_id: int = None
    ) -> BudgetLine:
        """
        Add budget line
        Migrated from gl210.cbl ADD-BUDGET-LINE
        """
        try:
            # Get budget
            budget = self.db.query(BudgetHeader).filter(
                BudgetHeader.id == budget_id
            ).first()
            if not budget:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Budget not found"
                )
            
            if budget.is_approved:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot modify approved budget"
                )
            
            # Get account
            account = self.db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == account_code
            ).first()
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Account {account_code} not found"
                )
            
            if not account.budget_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Account {account_code} is not budget-enabled"
                )
            
            # Check for existing line
            existing_line = self.db.query(BudgetLine).filter(
                and_(
                    BudgetLine.budget_id == budget_id,
                    BudgetLine.account_id == account.id
                )
            ).first()
            if existing_line:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Budget line already exists for account {account_code}"
                )
            
            # Calculate period amounts
            if spread_method == "CUSTOM" and period_amounts:
                if len(period_amounts) != 12:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Must provide 12 period amounts for custom spread"
                    )
                period_1 = period_amounts[0]
                period_2 = period_amounts[1]
                period_3 = period_amounts[2]
                period_4 = period_amounts[3]
                period_5 = period_amounts[4]
                period_6 = period_amounts[5]
                period_7 = period_amounts[6]
                period_8 = period_amounts[7]
                period_9 = period_amounts[8]
                period_10 = period_amounts[9]
                period_11 = period_amounts[10]
                period_12 = period_amounts[11]
            else:
                # Even spread
                period_amount = annual_amount / 12
                period_1 = period_amount
                period_2 = period_amount
                period_3 = period_amount
                period_4 = period_amount
                period_5 = period_amount
                period_6 = period_amount
                period_7 = period_amount
                period_8 = period_amount
                period_9 = period_amount
                period_10 = period_amount
                period_11 = period_amount
                period_12 = annual_amount - (period_amount * 11)  # Handle rounding
            
            # Create budget line
            budget_line = BudgetLine(
                budget_id=budget_id,
                account_id=account.id,
                account_code=account_code,
                annual_budget=annual_amount,
                period_1_budget=period_1,
                period_2_budget=period_2,
                period_3_budget=period_3,
                period_4_budget=period_4,
                period_5_budget=period_5,
                period_6_budget=period_6,
                period_7_budget=period_7,
                period_8_budget=period_8,
                period_9_budget=period_9,
                period_10_budget=period_10,
                period_11_budget=period_11,
                period_12_budget=period_12,
                notes=notes,
                created_by=str(user_id) if user_id else None
            )
            
            self.db.add(budget_line)
            
            # Update budget total
            budget.total_amount += annual_amount
            
            self.db.commit()
            self.db.refresh(budget_line)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="budget_lines",
                record_id=str(budget_line.id),
                operation="CREATE",
                user_id=user_id,
                details=f"Added budget line for account {account_code}, amount {annual_amount}"
            )
            
            return budget_line
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding budget line: {str(e)}"
            )
    
    def approve_budget(
        self,
        budget_id: int,
        user_id: int
    ) -> BudgetHeader:
        """
        Approve budget for use
        Migrated from gl200.cbl APPROVE-BUDGET
        """
        try:
            budget = self.db.query(BudgetHeader).filter(
                BudgetHeader.id == budget_id
            ).first()
            if not budget:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Budget not found"
                )
            
            if budget.is_approved:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Budget already approved"
                )
            
            # Validate budget has lines
            line_count = self.db.query(BudgetLine).filter(
                BudgetLine.budget_id == budget_id
            ).count()
            
            if line_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot approve budget with no lines"
                )
            
            # Approve budget
            budget.is_approved = True
            budget.approved_date = datetime.now()
            budget.approved_by = str(user_id)
            
            self.db.commit()
            self.db.refresh(budget)
            
            # Create audit trail
            self._create_audit_trail(
                table_name="budget_headers",
                record_id=str(budget.id),
                operation="APPROVE",
                user_id=user_id,
                details=f"Approved budget {budget.budget_name}"
            )
            
            return budget
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error approving budget: {str(e)}"
            )
    
    def copy_budget(
        self,
        source_budget_id: int,
        new_budget_name: str,
        new_fiscal_year: int,
        adjustment_percent: Optional[Decimal] = None,
        user_id: int = None
    ) -> BudgetHeader:
        """
        Copy budget to new year
        Migrated from gl220.cbl COPY-BUDGET
        """
        try:
            # Get source budget
            source = self.db.query(BudgetHeader).filter(
                BudgetHeader.id == source_budget_id
            ).first()
            if not source:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source budget not found"
                )
            
            # Create new budget
            new_budget = self.create_budget(
                budget_name=new_budget_name,
                fiscal_year=new_fiscal_year,
                budget_type=source.budget_type,
                description=f"Copied from {source.budget_name}",
                user_id=user_id
            )
            
            # Copy budget lines
            source_lines = self.db.query(BudgetLine).filter(
                BudgetLine.budget_id == source_budget_id
            ).all()
            
            adjustment = Decimal("1") + (adjustment_percent / 100 if adjustment_percent else 0)
            
            for source_line in source_lines:
                # Apply adjustment if specified
                annual_amount = source_line.annual_budget * adjustment
                period_amounts = [
                    source_line.period_1_budget * adjustment,
                    source_line.period_2_budget * adjustment,
                    source_line.period_3_budget * adjustment,
                    source_line.period_4_budget * adjustment,
                    source_line.period_5_budget * adjustment,
                    source_line.period_6_budget * adjustment,
                    source_line.period_7_budget * adjustment,
                    source_line.period_8_budget * adjustment,
                    source_line.period_9_budget * adjustment,
                    source_line.period_10_budget * adjustment,
                    source_line.period_11_budget * adjustment,
                    source_line.period_12_budget * adjustment
                ]
                
                self.add_budget_line(
                    budget_id=new_budget.id,
                    account_code=source_line.account_code,
                    annual_amount=annual_amount,
                    spread_method="CUSTOM",
                    period_amounts=period_amounts,
                    notes=source_line.notes,
                    user_id=user_id
                )
            
            self.db.refresh(new_budget)
            return new_budget
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error copying budget: {str(e)}"
            )
    
    def get_budget_variance_report(
        self,
        budget_id: int,
        period_id: Optional[int] = None,
        variance_threshold: Optional[Decimal] = None
    ) -> Dict:
        """
        Get budget vs actual variance report
        Migrated from gl220.cbl BUDGET-VARIANCE
        """
        try:
            # Get budget
            budget = self.db.query(BudgetHeader).filter(
                BudgetHeader.id == budget_id
            ).first()
            if not budget:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Budget not found"
                )
            
            # Get period
            if period_id:
                period = self.db.query(CompanyPeriod).filter(
                    CompanyPeriod.id == period_id
                ).first()
            else:
                period = self._get_current_period()
            
            if not period or period.year_number != budget.fiscal_year:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Period year does not match budget year"
                )
            
            # Get budget lines with actuals
            results = self.db.query(
                BudgetLine,
                AccountBalance,
                ChartOfAccounts
            ).join(
                ChartOfAccounts,
                BudgetLine.account_id == ChartOfAccounts.id
            ).outerjoin(
                AccountBalance,
                and_(
                    AccountBalance.account_id == BudgetLine.account_id,
                    AccountBalance.period_id == period.id
                )
            ).filter(
                BudgetLine.budget_id == budget_id
            ).all()
            
            # Calculate variances
            variance_lines = []
            total_budget_ytd = Decimal("0")
            total_actual_ytd = Decimal("0")
            
            for budget_line, balance, account in results:
                # Get budget amounts
                period_budget = self._get_period_budget(budget_line, period.period_number)
                ytd_budget = self._get_ytd_budget(budget_line, period.period_number)
                
                # Get actual amounts
                period_actual = (
                    balance.period_debits - balance.period_credits
                    if balance else Decimal("0")
                )
                
                # Calculate YTD actual
                ytd_actual = self._calculate_ytd_actual(
                    account.id, period.year_number, period.period_number
                )
                
                # Calculate variances
                period_variance = period_actual - period_budget
                period_variance_pct = (
                    (period_variance / period_budget * 100)
                    if period_budget != 0 else 0
                )
                
                ytd_variance = ytd_actual - ytd_budget
                ytd_variance_pct = (
                    (ytd_variance / ytd_budget * 100)
                    if ytd_budget != 0 else 0
                )
                
                # Apply threshold filter if specified
                if variance_threshold:
                    if abs(period_variance_pct) < variance_threshold:
                        continue
                
                variance_lines.append({
                    "account_code": account.account_code,
                    "account_name": account.account_name,
                    "period_budget": period_budget,
                    "period_actual": period_actual,
                    "period_variance": period_variance,
                    "period_variance_pct": period_variance_pct,
                    "ytd_budget": ytd_budget,
                    "ytd_actual": ytd_actual,
                    "ytd_variance": ytd_variance,
                    "ytd_variance_pct": ytd_variance_pct
                })
                
                total_budget_ytd += ytd_budget
                total_actual_ytd += ytd_actual
            
            total_variance = total_actual_ytd - total_budget_ytd
            total_variance_pct = (
                (total_variance / total_budget_ytd * 100)
                if total_budget_ytd != 0 else 0
            )
            
            return {
                "budget_name": budget.budget_name,
                "fiscal_year": budget.fiscal_year,
                "period": f"{period.period_number}/{period.year_number}",
                "variance_lines": variance_lines,
                "totals": {
                    "budget_ytd": total_budget_ytd,
                    "actual_ytd": total_actual_ytd,
                    "variance": total_variance,
                    "variance_pct": total_variance_pct
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating variance report: {str(e)}"
            )
    
    def _get_period_budget(self, budget_line: BudgetLine, period_number: int) -> Decimal:
        """Get budget amount for specific period"""
        period_map = {
            1: budget_line.period_1_budget,
            2: budget_line.period_2_budget,
            3: budget_line.period_3_budget,
            4: budget_line.period_4_budget,
            5: budget_line.period_5_budget,
            6: budget_line.period_6_budget,
            7: budget_line.period_7_budget,
            8: budget_line.period_8_budget,
            9: budget_line.period_9_budget,
            10: budget_line.period_10_budget,
            11: budget_line.period_11_budget,
            12: budget_line.period_12_budget
        }
        return period_map.get(period_number, Decimal("0"))
    
    def _get_ytd_budget(self, budget_line: BudgetLine, period_number: int) -> Decimal:
        """Get YTD budget amount"""
        total = Decimal("0")
        for period in range(1, period_number + 1):
            total += self._get_period_budget(budget_line, period)
        return total
    
    def _calculate_ytd_actual(
        self, account_id: int, year_number: int, period_number: int
    ) -> Decimal:
        """Calculate YTD actual amount"""
        ytd_result = self.db.query(
            func.sum(AccountBalance.period_debits - AccountBalance.period_credits)
        ).join(CompanyPeriod).filter(
            and_(
                AccountBalance.account_id == account_id,
                CompanyPeriod.year_number == year_number,
                CompanyPeriod.period_number <= period_number
            )
        ).scalar()
        
        return ytd_result or Decimal("0")