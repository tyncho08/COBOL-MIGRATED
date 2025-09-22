"""
ACAS Migrated Application Settings
Based on legacy ACAS system configuration
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
from decimal import Decimal as PyDecimal


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "ACAS Migrated"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Database Configuration
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: str = "5432"
    DATABASE_NAME: str = "acas_migrated"
    DATABASE_USER: str = "acas_user"
    DATABASE_PASSWORD: str
    
    # Database Pool Configuration
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ACAS Migrated API"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Security Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/acas-migrated/app.log"
    
    # File Storage
    UPLOAD_PATH: str = "/var/acas-migrated/uploads"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB
    
    # System Parameters (migrated from COBOL system.dat)
    DEFAULT_VAT_RATE: PyDecimal = PyDecimal("20.0")
    REDUCED_VAT_RATE: PyDecimal = PyDecimal("5.0")
    ZERO_VAT_RATE: PyDecimal = PyDecimal("0.0")
    DEFAULT_CURRENCY: str = "USD"
    FISCAL_YEAR_START_MONTH: int = 1
    STOCK_VALUATION_METHOD: str = "FIFO"
    CREDIT_CONTROL_ENABLED: bool = True
    MULTI_CURRENCY_ENABLED: bool = True
    
    # Business Rules (from ACAS system)
    CUSTOMER_CODE_LENGTH: int = 7
    STOCK_CODE_LENGTH: int = 13
    ACCOUNT_CODE_FORMAT: str = "####.####"
    INVOICE_NUMBER_PREFIX: str = ""
    ORDER_NUMBER_PREFIX: str = "ORD"
    
    # Period Processing
    ALLOW_BACK_DATED_TRANSACTIONS: bool = False
    MAX_OPEN_PERIODS: int = 2
    FORCE_PERIOD_CLOSE: bool = True
    
    # Credit Control
    DEFAULT_CREDIT_LIMIT: PyDecimal = PyDecimal("5000.00")
    CREDIT_CHECK_ENABLED: bool = True
    OVERDUE_DAYS_WARNING: int = 30
    OVERDUE_DAYS_STOP: int = 60
    
    # Stock Control
    ALLOW_NEGATIVE_STOCK: bool = False
    AUTO_REORDER_ENABLED: bool = True
    STOCK_TAKE_VARIANCE_LIMIT: PyDecimal = PyDecimal("5.0")  # Percentage
    
    # Financial Settings
    ROUNDING_METHOD: str = "ROUND_HALF_UP"
    DECIMAL_PLACES_QUANTITY: int = 2
    DECIMAL_PLACES_AMOUNT: int = 2
    DECIMAL_PLACES_RATE: int = 4
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env


settings = Settings()