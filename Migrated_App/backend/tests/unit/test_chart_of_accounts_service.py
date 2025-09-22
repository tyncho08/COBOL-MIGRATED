"""
Unit tests for Chart of Accounts Service
Tests the core business logic migrated from COBOL gl000.cbl, gl010.cbl, gl050.cbl
"""
import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.services.general_ledger.chart_of_accounts_service import ChartOfAccountsService
from app.models.general_ledger import ChartOfAccounts, AccountType


class TestChartOfAccountsService:
    """Test Chart of Accounts Service functionality"""

    def test_create_account_success(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test successful account creation"""
        service = ChartOfAccountsService(db)
        
        account = service.create_account(
            account_code="3000.0000",
            account_name="Owner's Equity",
            account_type=AccountType.CAPITAL,
            is_header=True,
            level=0,
            allow_posting=False,
            user_id=test_user_id
        )
        
        assert account is not None
        assert account.account_code == "3000.0000"
        assert account.account_name == "Owner's Equity"
        assert account.account_type == AccountType.CAPITAL
        assert account.is_header is True
        assert account.level == 0
        assert account.allow_posting is False
        assert account.is_active is True

    def test_create_account_duplicate_code(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test account creation with duplicate code"""
        service = ChartOfAccountsService(db)
        
        # Try to create account with existing code
        with pytest.raises(Exception):  # Should raise HTTPException for duplicate
            service.create_account(
                account_code="1000.0000",  # Already exists in sample data
                account_name="Duplicate Account",
                account_type=AccountType.ASSET,
                is_header=False,
                level=1,
                allow_posting=True,
                user_id=test_user_id
            )

    def test_create_account_invalid_code_format(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test account creation with invalid code format"""
        service = ChartOfAccountsService(db)
        
        with pytest.raises(Exception):  # Should raise HTTPException for invalid format
            service.create_account(
                account_code="INVALID",  # Invalid format
                account_name="Invalid Account",
                account_type=AccountType.ASSET,
                is_header=False,
                level=1,
                allow_posting=True,
                user_id=test_user_id
            )

    def test_create_sub_account_success(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test successful sub-account creation"""
        service = ChartOfAccountsService(db)
        
        sub_account = service.create_account(
            account_code="1000.0002",
            account_name="Petty Cash",
            account_type=AccountType.ASSET,
            parent_account="1000.0000",
            is_header=False,
            level=1,
            allow_posting=True,
            user_id=test_user_id
        )
        
        assert sub_account is not None
        assert sub_account.parent_account == "1000.0000"
        assert sub_account.level == 1
        assert sub_account.allow_posting is True

    def test_create_sub_account_invalid_parent(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test sub-account creation with invalid parent"""
        service = ChartOfAccountsService(db)
        
        with pytest.raises(Exception):  # Should raise HTTPException for invalid parent
            service.create_account(
                account_code="1000.0002",
                account_name="Sub Account",
                account_type=AccountType.ASSET,
                parent_account="9999.9999",  # Non-existent parent
                is_header=False,
                level=1,
                allow_posting=True,
                user_id=test_user_id
            )

    def test_update_account_success(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test successful account update"""
        service = ChartOfAccountsService(db)
        
        # Get existing account
        existing_account = sample_chart_of_accounts[0]  # "1000.0000"
        
        updates = {
            "account_name": "Updated Current Assets",
            "notes": "Updated description"
        }
        
        updated_account = service.update_account(
            existing_account.account_code,
            updates,
            test_user_id
        )
        
        assert updated_account.account_name == "Updated Current Assets"
        assert updated_account.notes == "Updated description"
        assert updated_account.updated_by == str(test_user_id)

    def test_update_account_not_found(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test updating non-existent account"""
        service = ChartOfAccountsService(db)
        
        updates = {"account_name": "Non-existent Account"}
        
        with pytest.raises(Exception):  # Should raise HTTPException for not found
            service.update_account(
                "9999.9999",  # Non-existent code
                updates,
                test_user_id
            )

    def test_deactivate_account_success(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test successful account deactivation"""
        service = ChartOfAccountsService(db)
        
        # Get account without children
        account_code = "1000.0001"  # Leaf account
        
        deactivated_account = service.deactivate_account(
            account_code,
            test_user_id
        )
        
        assert deactivated_account.is_active is False
        assert deactivated_account.updated_by == str(test_user_id)

    def test_deactivate_account_with_children(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test deactivating account with children"""
        service = ChartOfAccountsService(db)
        
        # Try to deactivate parent account
        with pytest.raises(Exception):  # Should raise HTTPException
            service.deactivate_account(
                "1000.0000",  # Has children
                test_user_id
            )

    def test_get_account_hierarchy(
        self, 
        db: Session, 
        sample_chart_of_accounts
    ):
        """Test getting account hierarchy"""
        service = ChartOfAccountsService(db)
        
        hierarchy = service.get_account_hierarchy()
        
        assert len(hierarchy) >= len(sample_chart_of_accounts)
        
        # Check that accounts are properly structured
        for account in hierarchy:
            if account["is_header"]:
                assert "children" in account
            assert "account_code" in account
            assert "account_name" in account
            assert "level" in account

    def test_get_accounts_by_type(
        self, 
        db: Session, 
        sample_chart_of_accounts
    ):
        """Test getting accounts by type"""
        service = ChartOfAccountsService(db)
        
        asset_accounts = service.get_accounts_by_type(AccountType.ASSET)
        
        assert len(asset_accounts) >= 2  # At least 2 asset accounts in sample data
        for account in asset_accounts:
            assert account.account_type == AccountType.ASSET

    def test_get_posting_accounts(
        self, 
        db: Session, 
        sample_chart_of_accounts
    ):
        """Test getting posting accounts only"""
        service = ChartOfAccountsService(db)
        
        posting_accounts = service.get_posting_accounts()
        
        assert len(posting_accounts) >= 1
        for account in posting_accounts:
            assert account.allow_posting is True
            assert account.is_header is False

    def test_search_accounts(
        self, 
        db: Session, 
        sample_chart_of_accounts
    ):
        """Test searching accounts"""
        service = ChartOfAccountsService(db)
        
        # Search by name
        results = service.search_accounts(
            search_term="Cash",
            page=1,
            page_size=10
        )
        
        assert "accounts" in results
        assert "total_count" in results
        assert results["total_count"] >= 1

    def test_validate_account_code_format(
        self, 
        db: Session
    ):
        """Test account code format validation"""
        service = ChartOfAccountsService(db)
        
        # Valid format
        assert service.validate_account_code_format("1000.0000") is True
        
        # Invalid formats
        assert service.validate_account_code_format("INVALID") is False
        assert service.validate_account_code_format("1000") is False
        assert service.validate_account_code_format("1000.00") is False
        assert service.validate_account_code_format("10000.0000") is False

    def test_get_account_balance(
        self, 
        db: Session, 
        sample_chart_of_accounts
    ):
        """Test getting account balance"""
        service = ChartOfAccountsService(db)
        
        # Get balance for existing account
        balance = service.get_account_balance("1000.0001")
        
        assert balance is not None
        assert "current_balance" in balance
        assert "ytd_movement" in balance
        assert "opening_balance" in balance

    def test_calculate_account_balances(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test calculating account balances"""
        service = ChartOfAccountsService(db)
        
        # Calculate balances for period
        results = service.calculate_account_balances(
            period_number=sample_company_period.period_number,
            year_number=sample_company_period.year_number
        )
        
        assert "processed_count" in results
        assert "updated_accounts" in results
        assert results["processed_count"] >= 0

    def test_get_trial_balance(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test generating trial balance"""
        service = ChartOfAccountsService(db)
        
        trial_balance = service.get_trial_balance(
            period_number=sample_company_period.period_number,
            year_number=sample_company_period.year_number
        )
        
        assert "accounts" in trial_balance
        assert "totals" in trial_balance
        assert "period_info" in trial_balance
        
        # Verify that debits equal credits
        totals = trial_balance["totals"]
        assert totals["total_debits"] == totals["total_credits"]

    def test_import_chart_of_accounts(
        self, 
        db: Session, 
        test_user_id
    ):
        """Test importing chart of accounts"""
        service = ChartOfAccountsService(db)
        
        accounts_data = [
            {
                "account_code": "4000.0000",
                "account_name": "Sales Revenue", 
                "account_type": "INCOME",
                "is_header": True,
                "level": 0,
                "allow_posting": False
            },
            {
                "account_code": "4000.0001",
                "account_name": "Product Sales",
                "account_type": "INCOME",
                "parent_account": "4000.0000",
                "is_header": False,
                "level": 1,
                "allow_posting": True
            }
        ]
        
        result = service.import_chart_of_accounts(
            accounts_data,
            test_user_id
        )
        
        assert "imported_count" in result
        assert "failed_count" in result
        assert "accounts" in result
        assert result["imported_count"] == 2
        assert result["failed_count"] == 0

    def test_export_chart_of_accounts(
        self, 
        db: Session, 
        sample_chart_of_accounts
    ):
        """Test exporting chart of accounts"""
        service = ChartOfAccountsService(db)
        
        export_data = service.export_chart_of_accounts()
        
        assert "accounts" in export_data
        assert "export_date" in export_data
        assert "total_count" in export_data
        
        assert len(export_data["accounts"]) >= len(sample_chart_of_accounts)

    def test_reorder_accounts(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test reordering accounts"""
        service = ChartOfAccountsService(db)
        
        # Test reordering within same parent
        reorder_data = [
            {
                "account_code": "1000.0001",
                "new_sort_order": 2
            }
        ]
        
        result = service.reorder_accounts(
            reorder_data,
            test_user_id
        )
        
        assert "updated_count" in result
        assert "accounts" in result

    def test_merge_accounts(
        self, 
        db: Session, 
        sample_chart_of_accounts,
        test_user_id
    ):
        """Test merging accounts"""
        service = ChartOfAccountsService(db)
        
        # Create two accounts to merge
        account1 = service.create_account(
            account_code="5000.0001",
            account_name="Office Expenses",
            account_type=AccountType.EXPENSE,
            is_header=False,
            level=1,
            allow_posting=True,
            user_id=test_user_id
        )
        
        account2 = service.create_account(
            account_code="5000.0002", 
            account_name="Administrative Expenses",
            account_type=AccountType.EXPENSE,
            is_header=False,
            level=1,
            allow_posting=True,
            user_id=test_user_id
        )
        
        # Merge account2 into account1
        result = service.merge_accounts(
            from_account_code=account2.account_code,
            to_account_code=account1.account_code,
            user_id=test_user_id
        )
        
        assert "merged_successfully" in result
        assert "transactions_moved" in result
        assert result["merged_successfully"] is True