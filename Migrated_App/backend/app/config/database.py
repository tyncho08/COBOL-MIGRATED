"""
Database Configuration
Handles PostgreSQL connection with advanced pooling
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from databases import Database
from .settings import settings

# Create async database instance for FastAPI
database = Database(settings.async_database_url)

# Create synchronous engine for Alembic migrations
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DEBUG,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Create metadata instance
metadata = MetaData()

# Custom type definitions matching COBOL data types
from sqlalchemy import types
from decimal import Decimal as PyDecimal

class COMP3(types.TypeDecorator):
    """COBOL COMP-3 (Packed Decimal) equivalent"""
    impl = types.Numeric
    cache_ok = True
    
    def __init__(self, precision=15, scale=2):
        super().__init__()
        self.precision = precision
        self.scale = scale
        self.impl = types.Numeric(precision=precision, scale=scale)

class CurrencyAmount(types.TypeDecorator):
    """Financial amount with 4 decimal precision"""
    impl = types.Numeric
    cache_ok = True
    
    def __init__(self):
        super().__init__()
        self.impl = types.Numeric(precision=15, scale=4)
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return PyDecimal(str(value))
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return PyDecimal(str(value))
        return value

class Percentage(types.TypeDecorator):
    """Percentage with 4 decimal precision"""
    impl = types.Numeric
    cache_ok = True
    
    def __init__(self):
        super().__init__()
        self.impl = types.Numeric(precision=5, scale=4)

class ExchangeRate(types.TypeDecorator):
    """Exchange rate with 6 decimal precision"""
    impl = types.Numeric
    cache_ok = True
    
    def __init__(self):
        super().__init__()
        self.impl = types.Numeric(precision=10, scale=6)

# Database dependency for FastAPI
async def get_db():
    """Dependency to get database session"""
    async with database.transaction():
        yield database