# ACAS Data Migration Scripts

This directory contains scripts for migrating data from the legacy COBOL ACAS system to the modern Python/PostgreSQL implementation.

## Overview

The migration process consists of two main phases:
1. **Data Migration** - Converting COBOL indexed files to PostgreSQL tables
2. **Data Validation** - Verifying integrity and completeness of migrated data

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Access to legacy COBOL data files
- Required Python packages (install from requirements.txt)

## Data Migration

### migrate_cobol_data.py

Main migration script that converts COBOL data files to PostgreSQL format.

#### Features
- Handles COBOL COMP-3 packed decimal conversion
- Preserves data integrity and business rules
- Supports incremental migration (skips existing records)
- Comprehensive error logging and recovery
- Progress tracking and statistics

#### Usage
```bash
python migrate_cobol_data.py --source /path/to/cobol/files --target postgresql://user:pass@host/db
```

#### Arguments
- `--source`: Path to directory containing COBOL data files
- `--target`: PostgreSQL database connection URL
- `--verbose`: Enable detailed logging

#### Supported COBOL Files
- **SUPPFILE.DAT** - Supplier Master File
- **CUSTFILE.DAT** - Customer Master File  
- **STOCKFILE.DAT** - Stock Master File
- **CHARTFILE.DAT** - Chart of Accounts File
- **POFILE.DAT** - Purchase Orders File (future)
- **SOFILE.DAT** - Sales Orders File (future)
- **GLFILE.DAT** - General Ledger File (future)

#### COBOL Record Layouts

##### Supplier Master (SUPPFILE)
```
Field               Position    Length    Type
SUPP-CODE          1-8         8         X(8)
SUPP-NAME          9-48        40        X(40)
CONTACT            49-78       30        X(30)
ADDRESS-LINE1      79-118      40        X(40)
ADDRESS-LINE2      119-158     40        X(40)
CITY               159-188     30        X(30)
POSTAL-CODE        189-208     20        X(20)
COUNTRY            209-228     20        X(20)
PHONE              229-248     20        X(20)
EMAIL              249-298     50        X(50)
PAYMENT-TERMS      299-308     10        X(10)
CURRENCY-CODE      309-311     3         X(3)
BALANCE            312-326     15        9(13)V99 COMP-3
STATUS-FLAG        327-327     1         X(1)
```

##### Customer Master (CUSTFILE)
```
Field               Position    Length    Type
CUST-CODE          1-8         8         X(8)
CUST-NAME          9-48        40        X(40)
CONTACT            49-78       30        X(30)
ADDRESS-LINE1      79-118      40        X(40)
ADDRESS-LINE2      119-158     40        X(40)
CITY               159-188     30        X(30)
POSTAL-CODE        189-208     20        X(20)
COUNTRY            209-228     20        X(20)
PHONE              229-248     20        X(20)
EMAIL              249-298     50        X(50)
PAYMENT-TERMS      299-308     10        X(10)
CURRENCY-CODE      309-311     3         X(3)
BALANCE            312-326     15        9(13)V99 COMP-3
CREDIT-LIMIT       327-341     15        9(13)V99 COMP-3
DISCOUNT-PERCENT   342-346     5         9(3)V99 COMP-3
STATUS-FLAG        347-347     1         X(1)
```

##### Stock Master (STOCKFILE)
```
Field               Position    Length    Type
STOCK-CODE         1-15        15        X(15)
DESCRIPTION        16-65       50        X(50)
CATEGORY-CODE      66-75       10        X(10)
UNIT-OF-MEASURE    76-85       10        X(10)
LOCATION           86-95       10        X(10)
QUANTITY-ON-HAND   96-110      15        9(12)V999 COMP-3
SELL-PRICE         111-125     15        9(13)V99 COMP-3
UNIT-COST          126-140     15        9(13)V99 COMP-3
VAT-CODE           141-142     2         X(2)
REORDER-POINT      143-157     15        9(12)V999 COMP-3
ECONOMIC-ORDER-QTY 158-172     15        9(12)V999 COMP-3
SUPPLIER-CODE      173-180     8         X(8)
STATUS-FLAG        181-181     1         X(1)
```

## Data Validation

### validate_migration.py

Comprehensive validation script that verifies the integrity and completeness of migrated data.

#### Features
- Record count validation against source files
- Data integrity constraint checking
- Business rule validation
- Referential integrity verification
- Financial balance validation
- Trial balance verification

#### Usage
```bash
python validate_migration.py --db postgresql://user:pass@host/db --source /path/to/cobol/files
```

#### Arguments
- `--db`: PostgreSQL database connection URL
- `--source`: Path to COBOL data files (optional, for count validation)
- `--verbose`: Enable detailed logging

#### Validation Checks

##### Record Count Validation
- Compares database record counts with source file counts
- Identifies missing or extra records

##### Data Integrity Validation
- Checks for duplicate primary keys
- Validates required field constraints
- Identifies orphaned records

##### Business Rule Validation
- Validates negative stock quantities
- Checks credit limit violations
- Verifies VAT code validity
- Validates cost and pricing rules

##### Referential Integrity Validation
- Verifies supplier-stock relationships
- Validates chart of accounts hierarchy
- Checks for circular references

##### Financial Balance Validation
- Validates account balance calculations
- Performs trial balance verification
- Checks stock valuation integrity

## Migration Process

### Step 1: Prepare Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up database
export DATABASE_URL="postgresql://user:password@localhost/acas_db"
```

### Step 2: Run Migration
```bash
# Run the migration
python scripts/migrate_cobol_data.py \
    --source /path/to/cobol/data \
    --target $DATABASE_URL \
    --verbose

# Check migration logs
tail -f migration.log
```

### Step 3: Validate Data
```bash
# Run validation
python scripts/validate_migration.py \
    --db $DATABASE_URL \
    --source /path/to/cobol/data \
    --verbose

# Check validation logs
tail -f validation.log
```

## Error Handling

### Migration Errors
- **File Format Errors**: Check COBOL file encoding (usually CP1252)
- **Data Type Errors**: Verify COMP-3 decimal parsing
- **Constraint Violations**: Review business rule implementations
- **Connection Errors**: Verify database connectivity and permissions

### Validation Errors
- **Record Count Mismatches**: Check for data filtering in migration
- **Integrity Violations**: Review referential integrity constraints
- **Balance Mismatches**: Verify decimal precision handling
- **Business Rule Violations**: Check legacy data quality

## Performance Optimization

### Large Dataset Migration
- Use batch processing (commits every 100 records)
- Enable connection pooling
- Disable foreign key checks during migration
- Use COPY commands for bulk inserts

### Memory Management
- Process files in chunks for large datasets
- Clear session cache periodically
- Use streaming for file processing

## Rollback and Recovery

### Backup Strategy
```bash
# Create pre-migration backup
pg_dump acas_db > backup_pre_migration.sql

# Create table-specific backups
pg_dump -t suppliers acas_db > suppliers_backup.sql
```

### Rollback Process
```bash
# Drop migrated data
TRUNCATE suppliers, customers, stock_items, chart_of_accounts CASCADE;

# Restore from backup
psql acas_db < backup_pre_migration.sql
```

## Monitoring and Logging

### Log Files
- **migration.log** - Migration process logs
- **validation.log** - Validation results
- **error.log** - Detailed error information

### Progress Monitoring
```bash
# Monitor migration progress
tail -f migration.log | grep "Processed"

# Check validation results
grep "ERROR\|WARNING" validation.log
```

## Testing

### Unit Tests
```bash
# Run migration script tests
python -m pytest tests/test_migration.py

# Run validation script tests  
python -m pytest tests/test_validation.py
```

### Integration Tests
```bash
# Test with sample data
python scripts/migrate_cobol_data.py \
    --source tests/sample_data \
    --target sqlite:///test.db
```

## Troubleshooting

### Common Issues

1. **Character Encoding Problems**
   - Solution: Specify correct encoding (cp1252, latin1, or utf-8)

2. **Decimal Conversion Errors**
   - Solution: Review COMP-3 field definitions and lengths

3. **Foreign Key Violations**
   - Solution: Migrate parent tables before child tables

4. **Performance Issues**
   - Solution: Increase batch sizes and optimize database settings

### Support

For issues or questions:
1. Check the log files for detailed error messages
2. Review the COBOL record layouts for field definitions
3. Verify database connectivity and permissions
4. Contact the development team with specific error details

## Migration Checklist

- [ ] Environment prepared and dependencies installed
- [ ] Database created and accessible
- [ ] COBOL data files identified and accessible
- [ ] Migration script tested with sample data
- [ ] Full migration executed successfully
- [ ] Validation script run and all checks passed
- [ ] Business users notified of completion
- [ ] Backup of migrated data created
- [ ] Legacy system archived or decommissioned