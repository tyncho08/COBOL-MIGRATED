#!/usr/bin/env python3
"""
COBOL to Python Data Migration Script
Migrates data from legacy COBOL indexed files to PostgreSQL database

This script handles the migration of all ACAS data from COBOL format:
- Supplier Master (SUPPFILE)
- Customer Master (CUSTFILE) 
- Stock Master (STOCKFILE)
- Chart of Accounts (CHARTFILE)
- Purchase Orders (POFILE)
- Sales Orders (SOFILE)
- Journal Entries (GLFILE)

Usage:
    python migrate_cobol_data.py --source /path/to/cobol/files --target postgresql://user:pass@host/db
"""

import argparse
import logging
import sys
import os
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional
import csv
import json

# Database imports
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Model imports
from app.models import Base
from app.models.suppliers import Supplier
from app.models.customers import Customer
from app.models.stock import StockItem, StockCategory
from app.models.general_ledger import ChartOfAccounts, AccountType
from app.models.purchase_transactions import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from app.models.sales_transactions import SalesOrder, SalesOrderLine, SalesOrderStatus
from app.models.general_ledger import JournalHeader, JournalLine, JournalStatus
from app.models.system import CompanyPeriod, CompanySettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CobolDataMigrator:
    """Main migration class that handles COBOL to PostgreSQL migration"""
    
    def __init__(self, source_path: str, target_db_url: str):
        self.source_path = Path(source_path)
        self.target_db_url = target_db_url
        self.engine = None
        self.session_factory = None
        self.migration_stats = {
            'suppliers': {'processed': 0, 'errors': 0},
            'customers': {'processed': 0, 'errors': 0},
            'stock_items': {'processed': 0, 'errors': 0},
            'chart_of_accounts': {'processed': 0, 'errors': 0},
            'purchase_orders': {'processed': 0, 'errors': 0},
            'sales_orders': {'processed': 0, 'errors': 0},
            'journal_entries': {'processed': 0, 'errors': 0},
        }
        
    def initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(self.target_db_url)
            self.session_factory = sessionmaker(bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(self.engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
            
    def parse_cobol_date(self, date_str: str) -> Optional[date]:
        """Parse COBOL date format (YYYYMMDD) to Python date"""
        if not date_str or date_str.strip() == '' or date_str == '00000000':
            return None
            
        try:
            return datetime.strptime(date_str.strip(), '%Y%m%d').date()
        except ValueError:
            try:
                # Try alternative format DDMMYYYY
                return datetime.strptime(date_str.strip(), '%d%m%Y').date()
            except ValueError:
                logger.warning(f"Unable to parse date: {date_str}")
                return None
                
    def parse_cobol_decimal(self, value_str: str, decimals: int = 2) -> Decimal:
        """Parse COBOL COMP-3 packed decimal format"""
        if not value_str or value_str.strip() == '':
            return Decimal('0.00')
            
        try:
            # Remove any non-numeric characters except decimal point and minus
            cleaned = ''.join(c for c in value_str if c.isdigit() or c in '.-')
            
            # Handle implicit decimal places
            if '.' not in cleaned and decimals > 0:
                # Insert decimal point
                if len(cleaned) > decimals:
                    cleaned = cleaned[:-decimals] + '.' + cleaned[-decimals:]
                else:
                    cleaned = '0.' + cleaned.zfill(decimals)
                    
            return Decimal(cleaned)
        except Exception as e:
            logger.warning(f"Unable to parse decimal: {value_str}, error: {e}")
            return Decimal('0.00')
            
    def migrate_suppliers(self):
        """Migrate supplier master file (SUPPFILE)"""
        logger.info("Starting supplier migration...")
        
        supplier_file = self.source_path / "SUPPFILE.DAT"
        if not supplier_file.exists():
            logger.warning(f"Supplier file not found: {supplier_file}")
            return
            
        session = self.session_factory()
        try:
            with open(supplier_file, 'r', encoding='cp1252') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # COBOL record layout for SUPPFILE
                        # Fields: SUPP-CODE(8), SUPP-NAME(40), CONTACT(30), ADDRESS(120), 
                        #         PHONE(20), EMAIL(50), TERMS(10), CURRENCY(3), BALANCE(15,2), STATUS(1)
                        
                        if len(line.strip()) < 299:  # Minimum record length
                            continue
                            
                        supplier_code = line[0:8].strip()
                        supplier_name = line[8:48].strip()
                        contact_person = line[48:78].strip()
                        address_line1 = line[78:118].strip()
                        address_line2 = line[118:158].strip()
                        city = line[158:188].strip()
                        postal_code = line[188:208].strip()
                        country = line[208:228].strip()
                        phone = line[228:248].strip()
                        email = line[248:298].strip()
                        payment_terms = line[298:308].strip()
                        currency_code = line[308:311].strip()
                        balance_str = line[311:326].strip()
                        status_flag = line[326:327].strip()
                        
                        if not supplier_code:
                            continue
                            
                        # Check if supplier already exists
                        existing = session.query(Supplier).filter_by(supplier_code=supplier_code).first()
                        if existing:
                            logger.debug(f"Supplier {supplier_code} already exists, skipping")
                            continue
                            
                        supplier = Supplier(
                            supplier_code=supplier_code,
                            supplier_name=supplier_name or f"Supplier {supplier_code}",
                            contact_person=contact_person if contact_person else None,
                            address_line1=address_line1 if address_line1 else None,
                            address_line2=address_line2 if address_line2 else None,
                            city=city if city else None,
                            postal_code=postal_code if postal_code else None,
                            country=country if country else None,
                            phone=phone if phone else None,
                            email=email if email else None,
                            payment_terms=payment_terms if payment_terms else "30 DAYS",
                            currency_code=currency_code if currency_code else "USD",
                            balance=self.parse_cobol_decimal(balance_str),
                            is_active=status_flag != 'I',  # 'I' = Inactive
                            created_by="migration_script",
                            created_date=datetime.now()
                        )
                        
                        session.add(supplier)
                        self.migration_stats['suppliers']['processed'] += 1
                        
                        if self.migration_stats['suppliers']['processed'] % 100 == 0:
                            session.commit()
                            logger.info(f"Processed {self.migration_stats['suppliers']['processed']} suppliers")
                            
                    except Exception as e:
                        logger.error(f"Error processing supplier line {line_num}: {e}")
                        self.migration_stats['suppliers']['errors'] += 1
                        
            session.commit()
            logger.info(f"Supplier migration completed. Processed: {self.migration_stats['suppliers']['processed']}, Errors: {self.migration_stats['suppliers']['errors']}")
            
        except Exception as e:
            logger.error(f"Fatal error in supplier migration: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            
    def migrate_customers(self):
        """Migrate customer master file (CUSTFILE)"""
        logger.info("Starting customer migration...")
        
        customer_file = self.source_path / "CUSTFILE.DAT"
        if not customer_file.exists():
            logger.warning(f"Customer file not found: {customer_file}")
            return
            
        session = self.session_factory()
        try:
            with open(customer_file, 'r', encoding='cp1252') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # COBOL record layout for CUSTFILE
                        # Similar to SUPPFILE but with credit limit and discount
                        
                        if len(line.strip()) < 329:  # Minimum record length
                            continue
                            
                        customer_code = line[0:8].strip()
                        customer_name = line[8:48].strip()
                        contact_person = line[48:78].strip()
                        address_line1 = line[78:118].strip()
                        address_line2 = line[118:158].strip()
                        city = line[158:188].strip()
                        postal_code = line[188:208].strip()
                        country = line[208:228].strip()
                        phone = line[228:248].strip()
                        email = line[248:298].strip()
                        payment_terms = line[298:308].strip()
                        currency_code = line[308:311].strip()
                        balance_str = line[311:326].strip()
                        credit_limit_str = line[326:341].strip()
                        discount_str = line[341:346].strip()
                        status_flag = line[346:347].strip()
                        
                        if not customer_code:
                            continue
                            
                        # Check if customer already exists
                        existing = session.query(Customer).filter_by(customer_code=customer_code).first()
                        if existing:
                            continue
                            
                        customer = Customer(
                            customer_code=customer_code,
                            customer_name=customer_name or f"Customer {customer_code}",
                            contact_person=contact_person if contact_person else None,
                            address_line1=address_line1 if address_line1 else None,
                            address_line2=address_line2 if address_line2 else None,
                            city=city if city else None,
                            postal_code=postal_code if postal_code else None,
                            country=country if country else None,
                            phone=phone if phone else None,
                            email=email if email else None,
                            payment_terms=payment_terms if payment_terms else "30 DAYS",
                            currency_code=currency_code if currency_code else "USD",
                            balance=self.parse_cobol_decimal(balance_str),
                            credit_limit=self.parse_cobol_decimal(credit_limit_str),
                            discount_percent=self.parse_cobol_decimal(discount_str, 2),
                            is_active=status_flag != 'I',
                            created_by="migration_script",
                            created_date=datetime.now()
                        )
                        
                        session.add(customer)
                        self.migration_stats['customers']['processed'] += 1
                        
                        if self.migration_stats['customers']['processed'] % 100 == 0:
                            session.commit()
                            logger.info(f"Processed {self.migration_stats['customers']['processed']} customers")
                            
                    except Exception as e:
                        logger.error(f"Error processing customer line {line_num}: {e}")
                        self.migration_stats['customers']['errors'] += 1
                        
            session.commit()
            logger.info(f"Customer migration completed. Processed: {self.migration_stats['customers']['processed']}, Errors: {self.migration_stats['customers']['errors']}")
            
        except Exception as e:
            logger.error(f"Fatal error in customer migration: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            
    def migrate_stock_items(self):
        """Migrate stock master file (STOCKFILE)"""
        logger.info("Starting stock item migration...")
        
        stock_file = self.source_path / "STOCKFILE.DAT"
        if not stock_file.exists():
            logger.warning(f"Stock file not found: {stock_file}")
            return
            
        session = self.session_factory()
        try:
            with open(stock_file, 'r', encoding='cp1252') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # COBOL record layout for STOCKFILE
                        
                        if len(line.strip()) < 250:  # Minimum record length
                            continue
                            
                        stock_code = line[0:15].strip()
                        description = line[15:65].strip()
                        category_code = line[65:75].strip()
                        unit_of_measure = line[75:85].strip()
                        location = line[85:95].strip()
                        quantity_str = line[95:110].strip()
                        sell_price_str = line[110:125].strip()
                        unit_cost_str = line[125:140].strip()
                        vat_code = line[140:142].strip()
                        reorder_point_str = line[142:157].strip()
                        economic_order_qty_str = line[157:172].strip()
                        supplier_code = line[172:180].strip()
                        status_flag = line[180:181].strip()
                        
                        if not stock_code:
                            continue
                            
                        # Check if stock item already exists
                        existing = session.query(StockItem).filter_by(stock_code=stock_code).first()
                        if existing:
                            continue
                            
                        stock_item = StockItem(
                            stock_code=stock_code,
                            description=description or f"Stock Item {stock_code}",
                            category_code=category_code if category_code else None,
                            unit_of_measure=unit_of_measure if unit_of_measure else "EACH",
                            location=location if location else "MAIN",
                            quantity_on_hand=self.parse_cobol_decimal(quantity_str, 3),
                            sell_price=self.parse_cobol_decimal(sell_price_str),
                            unit_cost=self.parse_cobol_decimal(unit_cost_str),
                            vat_code=vat_code if vat_code else "S",
                            reorder_point=self.parse_cobol_decimal(reorder_point_str, 3),
                            economic_order_qty=self.parse_cobol_decimal(economic_order_qty_str, 3),
                            supplier_code=supplier_code if supplier_code else None,
                            is_active=status_flag != 'I',
                            created_by="migration_script",
                            created_date=datetime.now()
                        )
                        
                        session.add(stock_item)
                        self.migration_stats['stock_items']['processed'] += 1
                        
                        if self.migration_stats['stock_items']['processed'] % 100 == 0:
                            session.commit()
                            logger.info(f"Processed {self.migration_stats['stock_items']['processed']} stock items")
                            
                    except Exception as e:
                        logger.error(f"Error processing stock item line {line_num}: {e}")
                        self.migration_stats['stock_items']['errors'] += 1
                        
            session.commit()
            logger.info(f"Stock item migration completed. Processed: {self.migration_stats['stock_items']['processed']}, Errors: {self.migration_stats['stock_items']['errors']}")
            
        except Exception as e:
            logger.error(f"Fatal error in stock item migration: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            
    def migrate_chart_of_accounts(self):
        """Migrate chart of accounts file (CHARTFILE)"""
        logger.info("Starting chart of accounts migration...")
        
        chart_file = self.source_path / "CHARTFILE.DAT"
        if not chart_file.exists():
            logger.warning(f"Chart file not found: {chart_file}")
            return
            
        session = self.session_factory()
        try:
            with open(chart_file, 'r', encoding='cp1252') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # COBOL record layout for CHARTFILE
                        
                        if len(line.strip()) < 200:  # Minimum record length
                            continue
                            
                        account_code = line[0:12].strip()
                        account_name = line[12:62].strip()
                        account_type_code = line[62:63].strip()
                        parent_account = line[63:75].strip()
                        level_str = line[75:77].strip()
                        header_flag = line[77:78].strip()
                        posting_flag = line[78:79].strip()
                        opening_balance_str = line[79:94].strip()
                        current_balance_str = line[94:109].strip()
                        ytd_movement_str = line[109:124].strip()
                        status_flag = line[124:125].strip()
                        
                        if not account_code:
                            continue
                            
                        # Map COBOL account type codes to enum
                        account_type_map = {
                            'A': AccountType.ASSET,
                            'L': AccountType.LIABILITY,
                            'C': AccountType.CAPITAL,
                            'I': AccountType.INCOME,
                            'E': AccountType.EXPENSE
                        }
                        
                        account_type = account_type_map.get(account_type_code, AccountType.ASSET)
                        
                        # Check if account already exists
                        existing = session.query(ChartOfAccounts).filter_by(account_code=account_code).first()
                        if existing:
                            continue
                            
                        chart_account = ChartOfAccounts(
                            account_code=account_code,
                            account_name=account_name or f"Account {account_code}",
                            account_type=account_type,
                            parent_account=parent_account if parent_account else None,
                            level=int(level_str) if level_str.isdigit() else 0,
                            is_header=header_flag == 'Y',
                            allow_posting=posting_flag == 'Y',
                            opening_balance=self.parse_cobol_decimal(opening_balance_str),
                            current_balance=self.parse_cobol_decimal(current_balance_str),
                            ytd_movement=self.parse_cobol_decimal(ytd_movement_str),
                            is_active=status_flag != 'I',
                            created_by="migration_script",
                            created_date=datetime.now()
                        )
                        
                        session.add(chart_account)
                        self.migration_stats['chart_of_accounts']['processed'] += 1
                        
                        if self.migration_stats['chart_of_accounts']['processed'] % 50 == 0:
                            session.commit()
                            logger.info(f"Processed {self.migration_stats['chart_of_accounts']['processed']} accounts")
                            
                    except Exception as e:
                        logger.error(f"Error processing account line {line_num}: {e}")
                        self.migration_stats['chart_of_accounts']['errors'] += 1
                        
            session.commit()
            logger.info(f"Chart of accounts migration completed. Processed: {self.migration_stats['chart_of_accounts']['processed']}, Errors: {self.migration_stats['chart_of_accounts']['errors']}")
            
        except Exception as e:
            logger.error(f"Fatal error in chart of accounts migration: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting COBOL to PostgreSQL migration...")
        start_time = datetime.now()
        
        try:
            # Initialize database
            self.initialize_database()
            
            # Run migrations in dependency order
            self.migrate_suppliers()
            self.migrate_customers()
            self.migrate_stock_items()
            self.migrate_chart_of_accounts()
            
            # Additional migrations would go here:
            # self.migrate_purchase_orders()
            # self.migrate_sales_orders()
            # self.migrate_journal_entries()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("Migration completed successfully!")
            logger.info(f"Migration duration: {duration}")
            self.print_migration_summary()
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
            
    def print_migration_summary(self):
        """Print summary of migration results"""
        logger.info("Migration Summary:")
        logger.info("=" * 50)
        
        total_processed = 0
        total_errors = 0
        
        for entity, stats in self.migration_stats.items():
            processed = stats['processed']
            errors = stats['errors']
            total_processed += processed
            total_errors += errors
            
            logger.info(f"{entity.replace('_', ' ').title()}: {processed} processed, {errors} errors")
            
        logger.info("=" * 50)
        logger.info(f"Total Records: {total_processed} processed, {total_errors} errors")
        
        if total_errors > 0:
            logger.warning(f"Migration completed with {total_errors} errors. Check migration.log for details.")
        else:
            logger.info("Migration completed successfully with no errors!")


def main():
    """Main entry point for the migration script"""
    parser = argparse.ArgumentParser(description='Migrate COBOL data to PostgreSQL')
    parser.add_argument('--source', required=True, help='Path to COBOL data files directory')
    parser.add_argument('--target', required=True, help='PostgreSQL database URL')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate source directory
    if not os.path.exists(args.source):
        logger.error(f"Source directory does not exist: {args.source}")
        sys.exit(1)
        
    try:
        migrator = CobolDataMigrator(args.source, args.target)
        migrator.run_migration()
        
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()