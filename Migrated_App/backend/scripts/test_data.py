#!/usr/bin/env python3
"""
Script de prueba para verificar datos en las tablas principales
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "postgresql://acas_user:secure-password-change-in-production@localhost:5432/acas_db"

def test_all_tables():
    """Verificar datos en las tablas principales"""
    engine = create_engine(DATABASE_URL)
    
    tables_to_check = [
        'customers',
        'suppliers', 
        'stock_items',
        'sales_orders',
        'purchase_orders',
        'gl_batches',
        'company_periods'
    ]
    
    print("📊 ACAS Database Data Verification")
    print("=" * 50)
    
    with engine.connect() as conn:
        for table in tables_to_check:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                
                # Get sample data
                sample_result = conn.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                samples = sample_result.fetchall()
                
                print(f"\n📋 {table.upper()}")
                print(f"   Records: {count}")
                
                if samples and count > 0:
                    columns = list(samples[0]._mapping.keys())[:5]  # First 5 columns
                    print(f"   Columns: {', '.join(columns)}")
                    
                    for i, sample in enumerate(samples[:2]):  # Show first 2 rows
                        values = []
                        for col in columns:
                            val = sample._mapping[col]
                            if val is not None:
                                str_val = str(val)
                                values.append(str_val[:20] + '...' if len(str_val) > 20 else str_val)
                            else:
                                values.append('NULL')
                        print(f"   Row {i+1}: {', '.join(values)}")
                else:
                    print(f"   ❌ NO DATA")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
    
    print(f"\n🎉 Verification completed!")


def test_gl_batches_specific():
    """Verificar específicamente los GL batches"""
    engine = create_engine(DATABASE_URL)
    
    print("\n🔍 GL BATCHES DETAILED CHECK")
    print("=" * 40)
    
    with engine.connect() as conn:
        # Verificar estructura
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'gl_batches' ORDER BY ordinal_position"))
        columns = result.fetchall()
        
        print("📋 GL Batches Table Structure:")
        for col in columns:
            print(f"   {col[0]}: {col[1]}")
        
        # Verificar datos
        print("\n📊 GL Batches Data:")
        result = conn.execute(text("""
            SELECT 
                batch_number,
                batch_type,
                description,
                is_balanced,
                is_posted,
                actual_debits,
                actual_credits,
                source_module
            FROM gl_batches 
            ORDER BY batch_number
        """))
        
        batches = result.fetchall()
        for batch in batches:
            print(f"   {batch[0]} | {batch[1]} | {batch[2][:30]}... | Balanced: {batch[3]} | Posted: {batch[4]}")


if __name__ == "__main__":
    test_all_tables()
    test_gl_batches_specific()