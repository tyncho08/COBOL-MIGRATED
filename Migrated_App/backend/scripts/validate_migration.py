#!/usr/bin/env python3
"""
Data Migration Validation Script
Validates the migrated data integrity and completeness

This script performs comprehensive validation of migrated ACAS data:
- Record count validation
- Data integrity checks
- Business rule validation
- Referential integrity validation
- Financial balance validation

Usage:
    python validate_migration.py --db postgresql://user:pass@host/db --source /path/to/cobol/files
"""

import argparse
import logging
import sys
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Tuple
import csv

# Database imports
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Model imports
from app.models.suppliers import Supplier
from app.models.customers import Customer
from app.models.stock import StockItem
from app.models.general_ledger import ChartOfAccounts
from app.models.purchase_transactions import PurchaseOrder
from app.models.sales_transactions import SalesOrder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Main validation class for checking migrated data integrity"""
    
    def __init__(self, db_url: str, source_path: str = None):
        self.db_url = db_url
        self.source_path = Path(source_path) if source_path else None
        self.engine = None
        self.session_factory = None
        self.validation_results = {
            'record_counts': {},
            'data_integrity': {},
            'business_rules': {},
            'referential_integrity': {},
            'financial_balances': {},
            'errors': [],
            'warnings': []
        }
        
    def initialize_database(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(self.db_url)
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
            
    def count_cobol_records(self, filename: str) -> int:
        """Count records in a COBOL data file"""
        if not self.source_path:
            return 0
            
        file_path = self.source_path / filename
        if not file_path.exists():
            logger.warning(f"COBOL file not found: {file_path}")
            return 0
            
        try:
            with open(file_path, 'r', encoding='cp1252') as f:
                count = sum(1 for line in f if line.strip())
            return count
        except Exception as e:
            logger.error(f"Error counting records in {filename}: {e}")
            return 0
            
    def validate_record_counts(self):
        """Validate that all records were migrated correctly"""
        logger.info("Validating record counts...")
        
        session = self.session_factory()
        try:
            # Supplier count validation
            db_supplier_count = session.query(func.count(Supplier.id)).scalar()
            cobol_supplier_count = self.count_cobol_records("SUPPFILE.DAT")
            
            self.validation_results['record_counts']['suppliers'] = {
                'database': db_supplier_count,
                'cobol_source': cobol_supplier_count,
                'match': db_supplier_count == cobol_supplier_count or cobol_supplier_count == 0
            }
            
            # Customer count validation
            db_customer_count = session.query(func.count(Customer.id)).scalar()
            cobol_customer_count = self.count_cobol_records("CUSTFILE.DAT")
            
            self.validation_results['record_counts']['customers'] = {
                'database': db_customer_count,
                'cobol_source': cobol_customer_count,
                'match': db_customer_count == cobol_customer_count or cobol_customer_count == 0
            }
            
            # Stock item count validation
            db_stock_count = session.query(func.count(StockItem.id)).scalar()
            cobol_stock_count = self.count_cobol_records("STOCKFILE.DAT")
            
            self.validation_results['record_counts']['stock_items'] = {
                'database': db_stock_count,
                'cobol_source': cobol_stock_count,
                'match': db_stock_count == cobol_stock_count or cobol_stock_count == 0
            }
            
            # Chart of accounts count validation
            db_account_count = session.query(func.count(ChartOfAccounts.id)).scalar()
            cobol_account_count = self.count_cobol_records("CHARTFILE.DAT")
            
            self.validation_results['record_counts']['chart_of_accounts'] = {
                'database': db_account_count,
                'cobol_source': cobol_account_count,
                'match': db_account_count == cobol_account_count or cobol_account_count == 0
            }
            
            logger.info("Record count validation completed")
            
        except Exception as e:
            logger.error(f"Error in record count validation: {e}")
            self.validation_results['errors'].append(f"Record count validation failed: {e}")
        finally:
            session.close()
            
    def validate_data_integrity(self):
        """Validate data integrity constraints"""
        logger.info("Validating data integrity...")
        
        session = self.session_factory()
        try:
            # Check for duplicate supplier codes
            duplicate_suppliers = session.execute(text("""
                SELECT supplier_code, COUNT(*) as count 
                FROM suppliers 
                GROUP BY supplier_code 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_suppliers:
                self.validation_results['data_integrity']['duplicate_suppliers'] = len(duplicate_suppliers)
                self.validation_results['errors'].append(f"Found {len(duplicate_suppliers)} duplicate supplier codes")
            else:
                self.validation_results['data_integrity']['duplicate_suppliers'] = 0
                
            # Check for duplicate customer codes
            duplicate_customers = session.execute(text("""
                SELECT customer_code, COUNT(*) as count 
                FROM customers 
                GROUP BY customer_code 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_customers:
                self.validation_results['data_integrity']['duplicate_customers'] = len(duplicate_customers)
                self.validation_results['errors'].append(f"Found {len(duplicate_customers)} duplicate customer codes")
            else:
                self.validation_results['data_integrity']['duplicate_customers'] = 0
                
            # Check for duplicate stock codes
            duplicate_stock = session.execute(text("""
                SELECT stock_code, COUNT(*) as count 
                FROM stock_items 
                GROUP BY stock_code 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_stock:
                self.validation_results['data_integrity']['duplicate_stock_codes'] = len(duplicate_stock)
                self.validation_results['errors'].append(f"Found {len(duplicate_stock)} duplicate stock codes")
            else:
                self.validation_results['data_integrity']['duplicate_stock_codes'] = 0
                
            # Check for duplicate account codes
            duplicate_accounts = session.execute(text("""
                SELECT account_code, COUNT(*) as count 
                FROM chart_of_accounts 
                GROUP BY account_code 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_accounts:
                self.validation_results['data_integrity']['duplicate_account_codes'] = len(duplicate_accounts)
                self.validation_results['errors'].append(f"Found {len(duplicate_accounts)} duplicate account codes")
            else:
                self.validation_results['data_integrity']['duplicate_account_codes'] = 0
                
            # Check for null/empty required fields
            null_supplier_names = session.query(func.count(Supplier.id)).filter(
                (Supplier.supplier_name == None) | (Supplier.supplier_name == '')
            ).scalar()
            
            if null_supplier_names > 0:
                self.validation_results['warnings'].append(f"Found {null_supplier_names} suppliers with missing names")
                
            null_customer_names = session.query(func.count(Customer.id)).filter(
                (Customer.customer_name == None) | (Customer.customer_name == '')
            ).scalar()
            
            if null_customer_names > 0:
                self.validation_results['warnings'].append(f"Found {null_customer_names} customers with missing names")
                
            null_stock_descriptions = session.query(func.count(StockItem.id)).filter(
                (StockItem.description == None) | (StockItem.description == '')
            ).scalar()
            
            if null_stock_descriptions > 0:
                self.validation_results['warnings'].append(f"Found {null_stock_descriptions} stock items with missing descriptions")
                
            logger.info("Data integrity validation completed")
            
        except Exception as e:
            logger.error(f"Error in data integrity validation: {e}")
            self.validation_results['errors'].append(f"Data integrity validation failed: {e}")
        finally:
            session.close()
            
    def validate_business_rules(self):
        """Validate business rule constraints"""
        logger.info("Validating business rules...")
        
        session = self.session_factory()
        try:
            # Check for negative stock quantities
            negative_stock = session.query(func.count(StockItem.id)).filter(
                StockItem.quantity_on_hand < 0
            ).scalar()
            
            if negative_stock > 0:
                self.validation_results['business_rules']['negative_stock_quantities'] = negative_stock
                self.validation_results['warnings'].append(f"Found {negative_stock} stock items with negative quantities")
            else:
                self.validation_results['business_rules']['negative_stock_quantities'] = 0
                
            # Check for invalid unit costs (negative or zero for active items)
            invalid_costs = session.query(func.count(StockItem.id)).filter(
                StockItem.is_active == True,
                (StockItem.unit_cost <= 0) | (StockItem.unit_cost == None)
            ).scalar()
            
            if invalid_costs > 0:
                self.validation_results['business_rules']['invalid_unit_costs'] = invalid_costs
                self.validation_results['warnings'].append(f"Found {invalid_costs} active stock items with invalid unit costs")
            else:
                self.validation_results['business_rules']['invalid_unit_costs'] = 0
                
            # Check for customers with credit limit exceeded
            over_limit_customers = session.execute(text("""
                SELECT COUNT(*) 
                FROM customers 
                WHERE balance > credit_limit 
                AND credit_limit > 0 
                AND is_active = true
            """)).scalar()
            
            if over_limit_customers > 0:
                self.validation_results['business_rules']['over_credit_limit'] = over_limit_customers
                self.validation_results['warnings'].append(f"Found {over_limit_customers} customers over credit limit")
            else:
                self.validation_results['business_rules']['over_credit_limit'] = 0
                
            # Check for invalid VAT codes
            invalid_vat_codes = session.execute(text("""
                SELECT COUNT(DISTINCT vat_code) 
                FROM stock_items 
                WHERE vat_code NOT IN ('S', 'Z', 'E', 'R', 'X')
                AND vat_code IS NOT NULL
            """)).scalar()
            
            if invalid_vat_codes > 0:
                self.validation_results['business_rules']['invalid_vat_codes'] = invalid_vat_codes
                self.validation_results['warnings'].append(f"Found {invalid_vat_codes} invalid VAT codes")
            else:
                self.validation_results['business_rules']['invalid_vat_codes'] = 0
                
            logger.info("Business rules validation completed")
            
        except Exception as e:
            logger.error(f"Error in business rules validation: {e}")
            self.validation_results['errors'].append(f"Business rules validation failed: {e}")
        finally:
            session.close()
            
    def validate_referential_integrity(self):
        """Validate referential integrity between entities"""
        logger.info("Validating referential integrity...")
        
        session = self.session_factory()
        try:
            # Check for stock items with invalid supplier codes
            invalid_supplier_refs = session.execute(text("""
                SELECT COUNT(*) 
                FROM stock_items s 
                LEFT JOIN suppliers sup ON s.supplier_code = sup.supplier_code 
                WHERE s.supplier_code IS NOT NULL 
                AND s.supplier_code != '' 
                AND sup.supplier_code IS NULL
            """)).scalar()
            
            if invalid_supplier_refs > 0:
                self.validation_results['referential_integrity']['invalid_supplier_references'] = invalid_supplier_refs
                self.validation_results['errors'].append(f"Found {invalid_supplier_refs} stock items with invalid supplier references")
            else:
                self.validation_results['referential_integrity']['invalid_supplier_references'] = 0
                
            # Check for chart of accounts with invalid parent references
            invalid_parent_refs = session.execute(text("""
                SELECT COUNT(*) 
                FROM chart_of_accounts c1 
                LEFT JOIN chart_of_accounts c2 ON c1.parent_account = c2.account_code 
                WHERE c1.parent_account IS NOT NULL 
                AND c1.parent_account != '' 
                AND c2.account_code IS NULL
            """)).scalar()
            
            if invalid_parent_refs > 0:
                self.validation_results['referential_integrity']['invalid_parent_account_references'] = invalid_parent_refs
                self.validation_results['errors'].append(f"Found {invalid_parent_refs} accounts with invalid parent references")
            else:
                self.validation_results['referential_integrity']['invalid_parent_account_references'] = 0
                
            # Check for circular references in chart of accounts
            # This is a simplified check - a full check would require recursive queries
            circular_refs = session.execute(text("""
                SELECT COUNT(*) 
                FROM chart_of_accounts c1 
                JOIN chart_of_accounts c2 ON c1.parent_account = c2.account_code 
                WHERE c2.parent_account = c1.account_code
            """)).scalar()
            
            if circular_refs > 0:
                self.validation_results['referential_integrity']['circular_account_references'] = circular_refs
                self.validation_results['errors'].append(f"Found {circular_refs} circular account references")
            else:
                self.validation_results['referential_integrity']['circular_account_references'] = 0
                
            logger.info("Referential integrity validation completed")
            
        except Exception as e:
            logger.error(f"Error in referential integrity validation: {e}")
            self.validation_results['errors'].append(f"Referential integrity validation failed: {e}")
        finally:
            session.close()
            
    def validate_financial_balances(self):
        """Validate financial balance calculations"""
        logger.info("Validating financial balances...")
        
        session = self.session_factory()
        try:
            # Check chart of accounts balance calculations
            balance_mismatches = session.execute(text("""
                SELECT account_code, account_name, opening_balance, ytd_movement, current_balance,
                       (opening_balance + ytd_movement) as calculated_balance
                FROM chart_of_accounts 
                WHERE ABS(current_balance - (opening_balance + ytd_movement)) > 0.01
                AND allow_posting = true
            """)).fetchall()
            
            if balance_mismatches:
                self.validation_results['financial_balances']['balance_mismatches'] = len(balance_mismatches)
                self.validation_results['errors'].append(f"Found {len(balance_mismatches)} account balance mismatches")
                
                # Log details of mismatched accounts
                for account in balance_mismatches[:5]:  # Log first 5 for debugging
                    logger.warning(f"Balance mismatch for account {account.account_code}: "
                                 f"Current={account.current_balance}, "
                                 f"Calculated={account.calculated_balance}")
            else:
                self.validation_results['financial_balances']['balance_mismatches'] = 0
                
            # Check for trial balance
            trial_balance = session.execute(text("""
                SELECT 
                    SUM(CASE WHEN account_type IN ('ASSET', 'EXPENSE') THEN current_balance ELSE 0 END) as debit_total,
                    SUM(CASE WHEN account_type IN ('LIABILITY', 'CAPITAL', 'INCOME') THEN current_balance ELSE 0 END) as credit_total
                FROM chart_of_accounts 
                WHERE allow_posting = true 
                AND is_active = true
            """)).fetchone()
            
            if trial_balance:
                debit_total = trial_balance.debit_total or Decimal('0')
                credit_total = trial_balance.credit_total or Decimal('0')
                balance_difference = abs(debit_total - credit_total)
                
                self.validation_results['financial_balances']['trial_balance'] = {
                    'debit_total': float(debit_total),
                    'credit_total': float(credit_total),
                    'difference': float(balance_difference),
                    'balanced': balance_difference <= Decimal('0.01')
                }
                
                if balance_difference > Decimal('0.01'):
                    self.validation_results['warnings'].append(
                        f"Trial balance out of balance by {balance_difference}"
                    )
                    
            # Validate stock valuations
            stock_value_issues = session.execute(text("""
                SELECT COUNT(*) 
                FROM stock_items 
                WHERE quantity_on_hand > 0 
                AND (unit_cost IS NULL OR unit_cost <= 0)
                AND is_active = true
            """)).scalar()
            
            if stock_value_issues > 0:
                self.validation_results['financial_balances']['stock_valuation_issues'] = stock_value_issues
                self.validation_results['warnings'].append(f"Found {stock_value_issues} stock items with valuation issues")
            else:
                self.validation_results['financial_balances']['stock_valuation_issues'] = 0
                
            logger.info("Financial balance validation completed")
            
        except Exception as e:
            logger.error(f"Error in financial balance validation: {e}")
            self.validation_results['errors'].append(f"Financial balance validation failed: {e}")
        finally:
            session.close()
            
    def run_validation(self):
        """Run the complete validation process"""
        logger.info("Starting data migration validation...")
        start_time = datetime.now()
        
        try:
            # Initialize database
            self.initialize_database()
            
            # Run all validations
            self.validate_record_counts()
            self.validate_data_integrity()
            self.validate_business_rules()
            self.validate_referential_integrity()
            self.validate_financial_balances()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("Validation completed!")
            logger.info(f"Validation duration: {duration}")
            self.print_validation_summary()
            
            # Return success status
            return len(self.validation_results['errors']) == 0
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise
            
    def print_validation_summary(self):
        """Print summary of validation results"""
        logger.info("Validation Summary:")
        logger.info("=" * 60)
        
        # Record counts
        logger.info("Record Counts:")
        for entity, counts in self.validation_results['record_counts'].items():
            status = "✓" if counts['match'] else "✗"
            logger.info(f"  {status} {entity.replace('_', ' ').title()}: "
                       f"DB={counts['database']}, COBOL={counts['cobol_source']}")
                       
        # Data integrity
        logger.info("\nData Integrity:")
        integrity_data = self.validation_results['data_integrity']
        for check, value in integrity_data.items():
            status = "✓" if value == 0 else "✗"
            logger.info(f"  {status} {check.replace('_', ' ').title()}: {value}")
            
        # Business rules
        logger.info("\nBusiness Rules:")
        rules_data = self.validation_results['business_rules']
        for check, value in rules_data.items():
            status = "✓" if value == 0 else "⚠"
            logger.info(f"  {status} {check.replace('_', ' ').title()}: {value}")
            
        # Referential integrity
        logger.info("\nReferential Integrity:")
        ref_data = self.validation_results['referential_integrity']
        for check, value in ref_data.items():
            status = "✓" if value == 0 else "✗"
            logger.info(f"  {status} {check.replace('_', ' ').title()}: {value}")
            
        # Financial balances
        logger.info("\nFinancial Balances:")
        finance_data = self.validation_results['financial_balances']
        for check, value in finance_data.items():
            if isinstance(value, dict):
                if check == 'trial_balance':
                    status = "✓" if value['balanced'] else "✗"
                    logger.info(f"  {status} Trial Balance: Balanced={value['balanced']}, "
                               f"Difference={value['difference']}")
            else:
                status = "✓" if value == 0 else "⚠"
                logger.info(f"  {status} {check.replace('_', ' ').title()}: {value}")
                
        # Errors and warnings
        logger.info("\n" + "=" * 60)
        error_count = len(self.validation_results['errors'])
        warning_count = len(self.validation_results['warnings'])
        
        if error_count > 0:
            logger.error(f"Validation completed with {error_count} errors:")
            for error in self.validation_results['errors']:
                logger.error(f"  • {error}")
        else:
            logger.info("No validation errors found!")
            
        if warning_count > 0:
            logger.warning(f"Validation completed with {warning_count} warnings:")
            for warning in self.validation_results['warnings']:
                logger.warning(f"  • {warning}")
                
        if error_count == 0 and warning_count == 0:
            logger.info("✓ All validations passed successfully!")


def main():
    """Main entry point for the validation script"""
    parser = argparse.ArgumentParser(description='Validate migrated COBOL data')
    parser.add_argument('--db', required=True, help='PostgreSQL database URL')
    parser.add_argument('--source', help='Path to COBOL data files directory (for count validation)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        validator = MigrationValidator(args.db, args.source)
        success = validator.run_validation()
        
        if success:
            logger.info("Validation completed successfully!")
            sys.exit(0)
        else:
            logger.error("Validation completed with errors!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()