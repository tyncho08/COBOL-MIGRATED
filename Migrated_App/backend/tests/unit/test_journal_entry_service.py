"""
Unit tests for Journal Entry Service  
Tests the core business logic migrated from COBOL gl100.cbl, gl110.cbl, gl200.cbl
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.services.general_ledger.journal_entry_service import JournalEntryService
from app.models.general_ledger import JournalHeader, JournalLine, JournalStatus


class TestJournalEntryService:
    """Test Journal Entry Service functionality"""

    def test_create_journal_entry_success(
        self, 
        db: Session, 
        sample_chart_of_accounts, 
        sample_company_period,
        test_user_id
    ):
        """Test successful journal entry creation"""
        service = JournalEntryService(db)
        
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "1000.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            },
            {
                "account_code": "2000.0001", 
                "debit_amount": "0.00",
                "credit_amount": "1000.00",
                "description": "Test credit entry"
            }
        ]
        
        journal = service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Test Journal Entry",
            reference="TEST001",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        assert journal is not None
        assert journal.journal_type == "MANUAL"
        assert journal.description == "Test Journal Entry"
        assert journal.reference == "TEST001"
        assert journal.status == JournalStatus.PENDING
        assert len(journal.journal_lines) == 2
        assert journal.total_debits == Decimal("1000.00")
        assert journal.total_credits == Decimal("1000.00")

    def test_create_journal_entry_unbalanced(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test journal entry creation with unbalanced entries"""
        service = JournalEntryService(db)
        
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "1000.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00", 
                "credit_amount": "500.00",  # Unbalanced
                "description": "Test credit entry"
            }
        ]
        
        with pytest.raises(Exception):  # Should raise HTTPException for unbalanced entry
            service.create_journal_entry(
                journal_date=date.today(),
                journal_type="MANUAL",
                description="Unbalanced Journal Entry",
                reference="TEST002",
                journal_lines=journal_lines,
                user_id=test_user_id
            )

    def test_create_journal_entry_invalid_account(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test journal entry creation with invalid account"""
        service = JournalEntryService(db)
        
        journal_lines = [
            {
                "account_code": "9999.9999",  # Invalid account
                "debit_amount": "1000.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            }
        ]
        
        with pytest.raises(Exception):  # Should raise HTTPException for invalid account
            service.create_journal_entry(
                journal_date=date.today(),
                journal_type="MANUAL",
                description="Invalid Account Journal",
                reference="TEST003",
                journal_lines=journal_lines,
                user_id=test_user_id
            )

    def test_create_journal_entry_non_posting_account(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test journal entry creation with non-posting account"""
        service = JournalEntryService(db)
        
        journal_lines = [
            {
                "account_code": "1000.0000",  # Header account (non-posting)
                "debit_amount": "1000.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            }
        ]
        
        with pytest.raises(Exception):  # Should raise HTTPException for non-posting account
            service.create_journal_entry(
                journal_date=date.today(),
                journal_type="MANUAL",
                description="Non-posting Account Journal",
                reference="TEST004",
                journal_lines=journal_lines,
                user_id=test_user_id
            )

    def test_post_journal_entry(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        sample_company_period,
        test_user_id
    ):
        """Test posting a journal entry"""
        service = JournalEntryService(db)
        
        # Create journal entry
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "1000.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "1000.00", 
                "description": "Test credit entry"
            }
        ]
        
        journal = service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Test Journal Entry",
            reference="TEST005",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        # Post the journal
        posted_journal = service.post_journal_entry(journal.id, test_user_id)
        
        assert posted_journal.status == JournalStatus.POSTED
        assert posted_journal.posted_by == str(test_user_id)
        assert posted_journal.posted_date is not None

    def test_reverse_journal_entry(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        sample_company_period,
        test_user_id
    ):
        """Test reversing a posted journal entry"""
        service = JournalEntryService(db)
        
        # Create and post journal entry
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "1000.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "1000.00",
                "description": "Test credit entry"
            }
        ]
        
        journal = service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Test Journal Entry",
            reference="TEST006",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        posted_journal = service.post_journal_entry(journal.id, test_user_id)
        
        # Reverse the journal
        reversal = service.reverse_journal_entry(
            posted_journal.id,
            reason="Error correction",
            user_id=test_user_id
        )
        
        assert reversal is not None
        assert reversal.journal_type == "REVERSAL"
        assert reversal.original_journal_id == posted_journal.id
        assert reversal.status == JournalStatus.POSTED
        
        # Check that debits and credits are reversed
        original_lines = posted_journal.journal_lines
        reversal_lines = reversal.journal_lines
        
        for i, original_line in enumerate(original_lines):
            reversal_line = reversal_lines[i]
            assert reversal_line.debit_amount == original_line.credit_amount
            assert reversal_line.credit_amount == original_line.debit_amount

    def test_get_journal_entries_by_period(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        sample_company_period,
        test_user_id
    ):
        """Test getting journal entries by period"""
        service = JournalEntryService(db)
        
        # Create a journal entry
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "500.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "500.00",
                "description": "Test credit entry"
            }
        ]
        
        service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Period Test Journal",
            reference="TEST007",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        # Get entries for the period
        entries = service.get_journal_entries_by_period(
            period_number=sample_company_period.period_number,
            year_number=sample_company_period.year_number,
            page=1,
            page_size=10
        )
        
        assert "journals" in entries
        assert "total_count" in entries
        assert entries["total_count"] >= 1
        assert len(entries["journals"]) >= 1

    def test_get_journal_entries_by_account(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test getting journal entries by account"""
        service = JournalEntryService(db)
        
        # Create journal entry
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "750.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "750.00",
                "description": "Test credit entry"
            }
        ]
        
        service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Account Test Journal",
            reference="TEST008",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        # Get entries for specific account
        entries = service.get_journal_entries_by_account(
            account_code="1000.0001",
            start_date=date.today(),
            end_date=date.today(),
            page=1,
            page_size=10
        )
        
        assert "journals" in entries
        assert "total_count" in entries
        assert entries["total_count"] >= 1

    def test_validate_journal_entry_dates(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test journal entry date validation"""
        service = JournalEntryService(db)
        
        # Test with future date
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "100.00",
                "credit_amount": "0.00",
                "description": "Future date test"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "100.00",
                "description": "Future date test"
            }
        ]
        
        from datetime import timedelta
        future_date = date.today() + timedelta(days=30)
        
        with pytest.raises(Exception):  # Should reject future dates
            service.create_journal_entry(
                journal_date=future_date,
                journal_type="MANUAL",
                description="Future Date Journal",
                reference="TEST009",
                journal_lines=journal_lines,
                user_id=test_user_id
            )

    def test_calculate_journal_totals(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test calculation of journal totals"""
        service = JournalEntryService(db)
        
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "1500.00",
                "credit_amount": "0.00",
                "description": "Debit line 1"
            },
            {
                "account_code": "1000.0001",
                "debit_amount": "500.00",
                "credit_amount": "0.00",
                "description": "Debit line 2"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "2000.00",
                "description": "Credit line"
            }
        ]
        
        journal = service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Multiple Lines Journal",
            reference="TEST010",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        assert journal.total_debits == Decimal("2000.00")
        assert journal.total_credits == Decimal("2000.00")
        assert len(journal.journal_lines) == 3

    def test_search_journal_entries(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test searching journal entries"""
        service = JournalEntryService(db)
        
        # Create journal entry with unique reference
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "250.00",
                "credit_amount": "0.00",
                "description": "Search test entry"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "250.00",
                "description": "Search test entry"
            }
        ]
        
        service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Searchable Journal Entry",
            reference="SEARCH001",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        # Search by reference
        results = service.search_journal_entries(
            search_term="SEARCH001",
            page=1,
            page_size=10
        )
        
        assert "journals" in results
        assert "total_count" in results
        assert results["total_count"] >= 1

    def test_get_trial_balance_data(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        sample_company_period,
        test_user_id
    ):
        """Test getting trial balance data"""
        service = JournalEntryService(db)
        
        # Create and post journal entries
        journal_lines = [
            {
                "account_code": "1000.0001",
                "debit_amount": "1000.00",
                "credit_amount": "0.00",
                "description": "Trial balance test"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "1000.00",
                "description": "Trial balance test"
            }
        ]
        
        journal = service.create_journal_entry(
            journal_date=date.today(),
            journal_type="MANUAL",
            description="Trial Balance Journal",
            reference="TB001",
            journal_lines=journal_lines,
            user_id=test_user_id
        )
        
        service.post_journal_entry(journal.id, test_user_id)
        
        # Get trial balance
        trial_balance = service.get_trial_balance_data(
            period_number=sample_company_period.period_number,
            year_number=sample_company_period.year_number
        )
        
        assert "accounts" in trial_balance
        assert "totals" in trial_balance
        assert trial_balance["totals"]["total_debits"] == trial_balance["totals"]["total_credits"]