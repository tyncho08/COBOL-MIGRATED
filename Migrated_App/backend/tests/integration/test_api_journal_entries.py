"""
Integration tests for Journal Entry API endpoints
Tests the complete API workflow from HTTP requests to database operations
"""
import pytest
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.general_ledger import JournalStatus


class TestJournalEntryAPI:
    """Test Journal Entry API endpoints"""

    def test_create_journal_entry_success(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test successful journal entry creation via API"""
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Test Journal Entry",
            "reference": "TEST001",
            "journal_lines": [
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
        }
        
        response = client.post("/api/v1/journal-entries/", json=journal_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["journal_type"] == "MANUAL"
        assert data["description"] == "Test Journal Entry"
        assert data["reference"] == "TEST001"
        assert data["status"] == JournalStatus.PENDING.value
        assert len(data["journal_lines"]) == 2
        assert data["total_debits"] == "1000.00"
        assert data["total_credits"] == "1000.00"

    def test_create_journal_entry_unbalanced(
        self, 
        client: TestClient, 
        sample_chart_of_accounts
    ):
        """Test journal entry creation with unbalanced entries"""
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Unbalanced Journal Entry",
            "reference": "TEST002",
            "journal_lines": [
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
        }
        
        response = client.post("/api/v1/journal-entries/", json=journal_data)
        
        assert response.status_code == 422
        assert "unbalanced" in response.json()["detail"].lower()

    def test_create_journal_entry_invalid_account(
        self, 
        client: TestClient
    ):
        """Test journal entry creation with invalid account"""
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Invalid Account Journal",
            "reference": "TEST003",
            "journal_lines": [
                {
                    "account_code": "9999.9999",  # Invalid account
                    "debit_amount": "1000.00",
                    "credit_amount": "0.00",
                    "description": "Test debit entry"
                }
            ]
        }
        
        response = client.post("/api/v1/journal-entries/", json=journal_data)
        
        assert response.status_code == 404
        assert "Account not found" in response.json()["detail"]

    def test_get_journal_entry_success(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test getting journal entry by ID"""
        # Create journal entry first
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Get Test Journal",
            "reference": "GET001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "500.00",
                    "credit_amount": "0.00",
                    "description": "Test debit"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "500.00",
                    "description": "Test credit"
                }
            ]
        }
        
        create_response = client.post("/api/v1/journal-entries/", json=journal_data)
        journal_id = create_response.json()["id"]
        
        # Get journal entry
        response = client.get(f"/api/v1/journal-entries/{journal_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == journal_id
        assert data["reference"] == "GET001"
        assert len(data["journal_lines"]) == 2

    def test_get_journal_entry_not_found(
        self, 
        client: TestClient
    ):
        """Test getting non-existent journal entry"""
        response = client.get("/api/v1/journal-entries/99999")
        
        assert response.status_code == 404
        assert "Journal entry not found" in response.json()["detail"]

    def test_post_journal_entry_success(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test posting a journal entry"""
        # Create journal entry first
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Post Test Journal",
            "reference": "POST001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "750.00",
                    "credit_amount": "0.00",
                    "description": "Test debit"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "750.00",
                    "description": "Test credit"
                }
            ]
        }
        
        create_response = client.post("/api/v1/journal-entries/", json=journal_data)
        journal_id = create_response.json()["id"]
        
        # Post the journal entry
        response = client.post(f"/api/v1/journal-entries/{journal_id}/post")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == JournalStatus.POSTED.value
        assert data["posted_date"] is not None

    def test_post_already_posted_journal(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test posting already posted journal entry"""
        # Create and post journal entry
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Already Posted Journal",
            "reference": "POST002",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "250.00",
                    "credit_amount": "0.00",
                    "description": "Test debit"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "250.00",
                    "description": "Test credit"
                }
            ]
        }
        
        create_response = client.post("/api/v1/journal-entries/", json=journal_data)
        journal_id = create_response.json()["id"]
        
        # First post
        client.post(f"/api/v1/journal-entries/{journal_id}/post")
        
        # Second post should fail
        response = client.post(f"/api/v1/journal-entries/{journal_id}/post")
        
        assert response.status_code == 400
        assert "already posted" in response.json()["detail"].lower()

    def test_reverse_journal_entry_success(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test reversing a posted journal entry"""
        # Create and post journal entry
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Reverse Test Journal",
            "reference": "REV001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "1250.00",
                    "credit_amount": "0.00",
                    "description": "Test debit"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "1250.00",
                    "description": "Test credit"
                }
            ]
        }
        
        create_response = client.post("/api/v1/journal-entries/", json=journal_data)
        journal_id = create_response.json()["id"]
        
        # Post the journal
        client.post(f"/api/v1/journal-entries/{journal_id}/post")
        
        # Reverse the journal
        reversal_data = {"reason": "Error correction"}
        response = client.post(
            f"/api/v1/journal-entries/{journal_id}/reverse",
            json=reversal_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["journal_type"] == "REVERSAL"
        assert data["original_journal_id"] == journal_id
        assert data["status"] == JournalStatus.POSTED.value

    def test_search_journal_entries(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test searching journal entries"""
        # Create journal entry with unique reference
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Searchable Journal Entry",
            "reference": "SEARCH001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "300.00",
                    "credit_amount": "0.00",
                    "description": "Search test"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "300.00",
                    "description": "Search test"
                }
            ]
        }
        
        client.post("/api/v1/journal-entries/", json=journal_data)
        
        # Search by reference
        response = client.get(
            "/api/v1/journal-entries/search",
            params={
                "search_term": "SEARCH001",
                "page": 1,
                "page_size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "journals" in data
        assert "total_count" in data
        assert data["total_count"] >= 1

    def test_get_journal_entries_by_period(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test getting journal entries by period"""
        response = client.get(
            "/api/v1/journal-entries/by-period",
            params={
                "period_number": sample_company_period.period_number,
                "year_number": sample_company_period.year_number,
                "page": 1,
                "page_size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "journals" in data
        assert "total_count" in data

    def test_get_journal_entries_by_account(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test getting journal entries by account"""
        # Create journal entry first
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Account Test Journal",
            "reference": "ACC001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "800.00",
                    "credit_amount": "0.00",
                    "description": "Account test"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "800.00",
                    "description": "Account test"
                }
            ]
        }
        
        client.post("/api/v1/journal-entries/", json=journal_data)
        
        # Get entries by account
        response = client.get(
            "/api/v1/journal-entries/by-account",
            params={
                "account_code": "1000.0001",
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
                "page": 1,
                "page_size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "journals" in data
        assert "total_count" in data

    def test_get_trial_balance(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test getting trial balance"""
        response = client.get(
            "/api/v1/journal-entries/trial-balance",
            params={
                "period_number": sample_company_period.period_number,
                "year_number": sample_company_period.year_number
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "totals" in data
        
        # Verify that debits equal credits
        totals = data["totals"]
        assert totals["total_debits"] == totals["total_credits"]

    def test_journal_entry_workflow_complete(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test complete journal entry workflow via API"""
        # 1. Create journal entry
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Complete Workflow Test",
            "reference": "WORKFLOW001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "1500.00",
                    "credit_amount": "0.00",
                    "description": "Workflow test debit"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "1500.00",
                    "description": "Workflow test credit"
                }
            ]
        }
        
        create_response = client.post("/api/v1/journal-entries/", json=journal_data)
        assert create_response.status_code == 201
        journal_id = create_response.json()["id"]
        
        # 2. Get journal details
        get_response = client.get(f"/api/v1/journal-entries/{journal_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == JournalStatus.PENDING.value
        
        # 3. Post journal entry
        post_response = client.post(f"/api/v1/journal-entries/{journal_id}/post")
        assert post_response.status_code == 200
        assert post_response.json()["status"] == JournalStatus.POSTED.value
        
        # 4. Reverse journal entry
        reversal_data = {"reason": "Workflow test reversal"}
        reverse_response = client.post(
            f"/api/v1/journal-entries/{journal_id}/reverse",
            json=reversal_data
        )
        assert reverse_response.status_code == 200
        
        reversal_id = reverse_response.json()["id"]
        
        # 5. Verify reversal was created
        reversal_get_response = client.get(f"/api/v1/journal-entries/{reversal_id}")
        assert reversal_get_response.status_code == 200
        reversal_data = reversal_get_response.json()
        assert reversal_data["journal_type"] == "REVERSAL"
        assert reversal_data["original_journal_id"] == journal_id

    def test_journal_entry_validation_errors(
        self, 
        client: TestClient, 
        sample_chart_of_accounts
    ):
        """Test various validation errors"""
        # Missing required fields
        invalid_data = {
            "journal_type": "MANUAL"
            # Missing journal_date, description, and journal_lines
        }
        
        response = client.post("/api/v1/journal-entries/", json=invalid_data)
        assert response.status_code == 422
        
        # Invalid date format
        invalid_date_data = {
            "journal_date": "invalid-date",
            "journal_type": "MANUAL",
            "description": "Invalid Date Test",
            "reference": "INVALID001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "100.00",
                    "credit_amount": "0.00",
                    "description": "Test"
                }
            ]
        }
        
        response = client.post("/api/v1/journal-entries/", json=invalid_date_data)
        assert response.status_code == 422

    def test_journal_entry_permissions(
        self, 
        client: TestClient, 
        sample_chart_of_accounts,
        sample_company_period
    ):
        """Test journal entry permissions and access control"""
        # Create journal entry
        journal_data = {
            "journal_date": date.today().isoformat(),
            "journal_type": "MANUAL",
            "description": "Permission Test Journal",
            "reference": "PERM001",
            "journal_lines": [
                {
                    "account_code": "1000.0001",
                    "debit_amount": "400.00",
                    "credit_amount": "0.00",
                    "description": "Permission test"
                },
                {
                    "account_code": "2000.0001",
                    "debit_amount": "0.00",
                    "credit_amount": "400.00",
                    "description": "Permission test"
                }
            ]
        }
        
        create_response = client.post("/api/v1/journal-entries/", json=journal_data)
        assert create_response.status_code == 201
        
        # All operations should succeed for now (no auth implemented yet)
        journal_id = create_response.json()["id"]
        
        post_response = client.post(f"/api/v1/journal-entries/{journal_id}/post")
        assert post_response.status_code == 200