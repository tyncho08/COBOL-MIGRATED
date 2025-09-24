#!/usr/bin/env python3
"""
Script para poblar la tabla gl_batches con datos de ejemplo
"""
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from decimal import Decimal

# Database connection
DATABASE_URL = "postgresql://acas_user:secure-password-change-in-production@localhost:5432/acas_db"

def populate_gl_batches():
    """Poplar gl_batches con datos de ejemplo"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Verificar si ya hay datos
        result = conn.execute(text("SELECT COUNT(*) FROM gl_batches"))
        count = result.scalar()
        
        if count > 0:
            print(f"⚠ GL Batches ya tiene {count} registros. Agregando más datos...")
        
        # Insertar datos de ejemplo
        sample_batches = [
            {
                'batch_number': 'GL2024001',
                'batch_date': '2024-01-15',
                'batch_type': 'JOURNAL',
                'description': 'Monthly depreciation entries',
                'source_module': 'GL',
                'period_id': 3,
                'control_count': 25,
                'control_debits': Decimal('15000.00'),
                'control_credits': Decimal('15000.00'),
                'actual_count': 25,
                'actual_debits': Decimal('15000.00'),
                'actual_credits': Decimal('15000.00'),
                'is_balanced': True,
                'is_posted': True,
                'posted_date': '2024-01-15',
                'posted_by': 'SYSTEM',
                'created_by': 'ADMIN',
                'updated_by': 'ADMIN'
            },
            {
                'batch_number': 'GL2024002',
                'batch_date': '2024-01-16',
                'batch_type': 'ACCRUAL',
                'description': 'Month-end accruals',
                'source_module': 'GL',
                'period_id': 3,
                'control_count': 15,
                'control_debits': Decimal('8500.00'),
                'control_credits': Decimal('8500.00'),
                'actual_count': 15,
                'actual_debits': Decimal('8500.00'),
                'actual_credits': Decimal('8500.00'),
                'is_balanced': True,
                'is_posted': False,
                'created_by': 'ADMIN',
                'updated_by': 'ADMIN'
            },
            {
                'batch_number': 'GL2024003',
                'batch_date': '2024-01-17',
                'batch_type': 'CORRECTION',
                'description': 'Correction of posting errors',
                'source_module': 'GL',
                'period_id': 3,
                'control_count': 8,
                'control_debits': Decimal('2500.00'),
                'control_credits': Decimal('2300.00'),
                'actual_count': 8,
                'actual_debits': Decimal('2500.00'),
                'actual_credits': Decimal('2300.00'),
                'is_balanced': False,
                'is_posted': False,
                'created_by': 'ADMIN',
                'updated_by': 'ADMIN'
            },
            {
                'batch_number': 'AP2024001',
                'batch_date': '2024-01-18',
                'batch_type': 'INVOICE',
                'description': 'Supplier invoice batch',
                'source_module': 'AP',
                'period_id': 3,
                'control_count': 35,
                'control_debits': Decimal('12500.00'),
                'control_credits': Decimal('12500.00'),
                'actual_count': 35,
                'actual_debits': Decimal('12500.00'),
                'actual_credits': Decimal('12500.00'),
                'is_balanced': True,
                'is_posted': True,
                'posted_date': '2024-01-18',
                'posted_by': 'SYSTEM',
                'created_by': 'ADMIN',
                'updated_by': 'ADMIN'
            },
            {
                'batch_number': 'AR2024001',
                'batch_date': '2024-01-19',
                'batch_type': 'INVOICE',
                'description': 'Customer invoice batch',
                'source_module': 'AR',
                'period_id': 3,
                'control_count': 42,
                'control_debits': Decimal('18750.00'),
                'control_credits': Decimal('18750.00'),
                'actual_count': 42,
                'actual_debits': Decimal('18750.00'),
                'actual_credits': Decimal('18750.00'),
                'is_balanced': True,
                'is_posted': False,
                'created_by': 'ADMIN',
                'updated_by': 'ADMIN'
            }
        ]
        
        for batch in sample_batches:
            # Verificar si el batch ya existe
            check = conn.execute(text("SELECT id FROM gl_batches WHERE batch_number = :batch_number"), 
                               {"batch_number": batch['batch_number']})
            if check.fetchone():
                print(f"⚠ Batch {batch['batch_number']} already exists, skipping...")
                continue
            
            # Insertar el batch
            insert_sql = text("""
                INSERT INTO gl_batches (
                    batch_number, batch_date, batch_type, description, source_module,
                    period_id, control_count, control_debits, control_credits,
                    actual_count, actual_debits, actual_credits, is_balanced, is_posted,
                    posted_date, posted_by, created_by, updated_by, created_at, updated_at
                ) VALUES (
                    :batch_number, :batch_date, :batch_type, :description, :source_module,
                    :period_id, :control_count, :control_debits, :control_credits,
                    :actual_count, :actual_debits, :actual_credits, :is_balanced, :is_posted,
                    :posted_date, :posted_by, :created_by, :updated_by, NOW(), NOW()
                )
            """)
            
            conn.execute(insert_sql, batch)
            print(f"✅ Inserted batch: {batch['batch_number']}")
        
        conn.commit()
        
        # Verificar resultado
        result = conn.execute(text("SELECT COUNT(*) FROM gl_batches"))
        final_count = result.scalar()
        print(f"\n🎉 Successfully populated gl_batches. Total records: {final_count}")


def main():
    print("ACAS GL Batches Population Script")
    print("=" * 40)
    
    try:
        populate_gl_batches()
        print("\n✅ GL Batches population completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during population: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()