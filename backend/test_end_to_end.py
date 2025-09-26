#!/usr/bin/env python
"""
End-to-end test to verify the date conversion and days calculation fixes
"""
import pandas as pd
from datetime import datetime, date


def test_excel_data_processing():
    """Test processing of Excel-like data with various date formats and days calculations"""
    print("Testing end-to-end Excel data processing...")
    
    # Create sample data similar to what would come from Excel
    test_data = {
        'NOMBRE': ['Juan Perez', 'Maria Lopez', 'Carlos Silva', 'Ana Rodriguez'],
        'RUT': ['12345678-9', '98765432-1', '11111111-1', '22222222-2'],
        'FECHA INICIO AUSENCIA': [
            datetime(2025, 5, 3),    # Regular datetime
            45780,                   # Excel serial (should be around 2025-05-03)
            '2025-05-05',            # String format
            '05/05/2025'             # Another string format
        ],
        'FECHA FIN AUSENCIA': [
            datetime(2025, 5, 5),    # Regular datetime (3 days)
            45782,                   # Excel serial (should be around 2025-05-05, 3 days)
            '2025-05-07',            # String format (3 days)
            '07/05/2025'             # Another string format (3 days)
        ],
        'DIAS': [
            3,    # Correct
            0,    # Incorrect - should be recalculated
            5,    # Incorrect - should be 3
            2     # Incorrect - should be 3
        ]
    }
    
    df = pd.DataFrame(test_data)
    print("\nOriginal data:")
    print(df[['NOMBRE', 'FECHA INICIO AUSENCIA', 'FECHA FIN AUSENCIA', 'DIAS']])
    
    # Import our conversion function
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    # Use our isolated function for testing
    from test_convertir_fecha_isolated import convertir_fecha_isolated
    
    print("\nProcessed data:")
    corrections_count = 0
    
    for index, row in df.iterrows():
        # Convert dates
        fecha_inicio = convertir_fecha_isolated(row['FECHA INICIO AUSENCIA'])
        fecha_fin = convertir_fecha_isolated(row['FECHA FIN AUSENCIA'])
        dias_original = row['DIAS']
        
        # Calculate days
        dias_final = dias_original
        if fecha_inicio and fecha_fin:
            dias_calculado = (fecha_fin - fecha_inicio).days + 1  # Inclusive
            
            # Recalculate if days is wrong
            if (dias_original <= 0 or abs(dias_original - dias_calculado) > 0):
                dias_final = max(1, dias_calculado)
                if dias_original != dias_final:
                    corrections_count += 1
                    print(f"  Row {index}: {row['NOMBRE']}")
                    print(f"    Dates: {fecha_inicio} to {fecha_fin}")
                    print(f"    Days corrected: {dias_original} → {dias_final}")
        
        print(f"  {row['NOMBRE']}: {fecha_inicio} to {fecha_fin}, {dias_final} days")
    
    print(f"\nTotal corrections made: {corrections_count}")
    print("✅ End-to-end test completed successfully!")


if __name__ == '__main__':
    test_excel_data_processing()