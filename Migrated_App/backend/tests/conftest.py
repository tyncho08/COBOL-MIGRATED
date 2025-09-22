"""
Test configuration and fixtures for ACAS backend testing
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import *  # Import all models
from decimal import Decimal
from datetime import datetime, date

# Test database URL - using SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create and provide a database session for testing"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_supplier(db: Session):
    """Create a sample supplier for testing"""
    from app.models.suppliers import Supplier
    
    supplier = Supplier(
        supplier_code="TEST001",
        supplier_name="Test Supplier Ltd",
        contact_person="John Smith",
        address_line1="123 Test Street",
        city="Test City",
        postal_code="12345",
        country="USA",
        phone="555-0123",
        email="test@supplier.com",
        payment_terms="30 DAYS",
        currency_code="USD",
        balance=Decimal("0"),
        is_active=True,
        created_by="test_user"
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@pytest.fixture
def sample_customer(db: Session):
    """Create a sample customer for testing"""
    from app.models.customers import Customer
    
    customer = Customer(
        customer_code="CUST001",
        customer_name="Test Customer Inc",
        contact_person="Jane Doe",
        address_line1="456 Customer Ave",
        city="Customer City",
        postal_code="54321",
        country="USA",
        phone="555-0456",
        email="test@customer.com",
        payment_terms="30 DAYS",
        currency_code="USD",
        balance=Decimal("0"),
        credit_limit=Decimal("10000"),
        discount_percent=Decimal("5"),
        is_active=True,
        created_by="test_user"
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def sample_stock_item(db: Session):
    """Create a sample stock item for testing"""
    from app.models.stock import StockItem
    
    stock_item = StockItem(
        stock_code="TEST001",
        description="Test Stock Item",
        category_code="TEST",
        unit_of_measure="EACH",
        location="MAIN",
        quantity_on_hand=Decimal("100"),
        sell_price=Decimal("50.00"),
        unit_cost=Decimal("30.00"),
        vat_code="S",
        reorder_point=Decimal("10"),
        economic_order_qty=Decimal("50"),
        is_active=True,
        created_by="test_user"
    )
    db.add(stock_item)
    db.commit()
    db.refresh(stock_item)
    return stock_item


@pytest.fixture
def sample_chart_of_accounts(db: Session):
    """Create sample chart of accounts for testing"""
    from app.models.general_ledger import ChartOfAccounts, AccountType
    
    accounts = [
        ChartOfAccounts(
            account_code="1000.0000",
            account_name="Current Assets",
            account_type=AccountType.ASSET,
            is_header=True,
            level=0,
            allow_posting=False,
            is_active=True,
            opening_balance=Decimal("0"),
            current_balance=Decimal("0"),
            ytd_movement=Decimal("0"),
            created_by="test_user"
        ),
        ChartOfAccounts(
            account_code="1000.0001",
            account_name="Cash at Bank",
            account_type=AccountType.ASSET,
            parent_account="1000.0000",
            is_header=False,
            level=1,
            allow_posting=True,
            is_active=True,
            opening_balance=Decimal("0"),
            current_balance=Decimal("10000"),
            ytd_movement=Decimal("1000"),
            created_by="test_user"
        ),
        ChartOfAccounts(
            account_code="2000.0000",
            account_name="Current Liabilities",
            account_type=AccountType.LIABILITY,
            is_header=True,
            level=0,
            allow_posting=False,
            is_active=True,
            opening_balance=Decimal("0"),
            current_balance=Decimal("0"),
            ytd_movement=Decimal("0"),
            created_by="test_user"
        )
    ]
    
    for account in accounts:
        db.add(account)
    db.commit()
    
    for account in accounts:
        db.refresh(account)
    
    return accounts


@pytest.fixture
def sample_company_period(db: Session):
    """Create a sample company period for testing"""
    from app.models.system import CompanyPeriod
    
    period = CompanyPeriod(
        period_number=1,
        year_number=2024,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        is_open=True,
        is_current=True,
        created_by="test_user"
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


@pytest.fixture
def sample_purchase_order(db: Session, sample_supplier: "Supplier"):
    """Create a sample purchase order for testing"""
    from app.models.purchase_transactions import PurchaseOrder, PurchaseOrderStatus
    
    po = PurchaseOrder(
        order_number="PO000001",
        supplier_id=sample_supplier.id,
        supplier_code=sample_supplier.supplier_code,
        order_date=date.today(),
        order_status=PurchaseOrderStatus.PENDING,
        gross_amount=Decimal("1000.00"),
        vat_amount=Decimal("200.00"),
        net_amount=Decimal("1200.00"),
        created_by="test_user"
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


@pytest.fixture
def test_user_id():
    """Return a test user ID"""
    return 1


# Sample data for various tests
@pytest.fixture
def sample_journal_entry_data():
    """Sample data for creating journal entries"""
    return {
        "journal_date": date.today(),
        "journal_type": "MANUAL",
        "description": "Test Journal Entry",
        "reference": "TEST001",
        "journal_lines": [
            {
                "account_code": "1000.0001",
                "debit_amount": "100.00",
                "credit_amount": "0.00",
                "description": "Test debit entry"
            },
            {
                "account_code": "2000.0001",
                "debit_amount": "0.00",
                "credit_amount": "100.00",
                "description": "Test credit entry"
            }
        ]
    }


@pytest.fixture
def sample_budget_data():
    """Sample data for creating budgets"""
    return {
        "budget_name": "Test Budget 2024",
        "fiscal_year": 2024,
        "budget_type": "ANNUAL",
        "description": "Test budget for 2024"
    }