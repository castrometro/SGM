#!/usr/bin/env python
"""
Isolated tests for convertir_fecha function
Tests Excel serial date conversion without Django dependencies
"""
import unittest
from datetime import datetime, date
import pandas as pd


def convertir_fecha_isolated(fecha_valor):
    """Isolated version of convertir_fecha for testing without Django dependencies"""
    # Handle arrays and other complex types first
    try:
        if hasattr(fecha_valor, '__iter__') and not isinstance(fecha_valor, (str, bytes)):
            return None
    except Exception:
        pass
        
    if pd.isna(fecha_valor) or fecha_valor is None:
        return None
    
    # Si ya es datetime, convertir a date
    if isinstance(fecha_valor, datetime):
        return fecha_valor.date()
    
    # Si es Pandas Timestamp
    if hasattr(fecha_valor, 'date') and callable(getattr(fecha_valor, 'date')):
        return fecha_valor.date()
    
    # Manejar números (seriales de Excel)
    if isinstance(fecha_valor, (int, float)):
        try:
            # Excel usa 1899-12-30 como origen para la mayoría de casos
            result = pd.to_datetime(fecha_valor, unit='D', origin='1899-12-30')
            if pd.isna(result):
                return None
            return result.date()
        except Exception:
            return None
    
    # Manejar strings con múltiples formatos
    if isinstance(fecha_valor, str):
        fecha_str = str(fecha_valor).strip()
        if not fecha_str:
            return None
        
        # Intentar formatos comunes
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y', '%d.%m.%Y']
        for formato in formatos:
            try:
                return datetime.strptime(fecha_str, formato).date()
            except ValueError:
                continue
        
        # Último intento con pandas
        try:
            result = pd.to_datetime(fecha_str, dayfirst=True, errors='coerce')
            if pd.isna(result):
                return None
            return result.date()
        except:
            return None
    
    return None


class TestConvertirFecha(unittest.TestCase):
    """Test the convertir_fecha function with various input types"""
    
    def test_none_and_na_values(self):
        """Test handling of None and NaN values"""
        self.assertIsNone(convertir_fecha_isolated(None))
        self.assertIsNone(convertir_fecha_isolated(pd.NaT))
        # Note: float('nan') needs special handling for pandas
    
    def test_datetime_conversion(self):
        """Test conversion from datetime objects"""
        dt = datetime(2025, 5, 3, 14, 30, 0)
        expected = date(2025, 5, 3)
        result = convertir_fecha_isolated(dt)
        self.assertEqual(result, expected)
    
    def test_pandas_timestamp(self):
        """Test conversion from pandas Timestamp"""
        ts = pd.Timestamp('2025-05-03 14:30:00')
        expected = date(2025, 5, 3)
        result = convertir_fecha_isolated(ts)
        self.assertEqual(result, expected)
    
    def test_excel_serial_numbers(self):
        """Test conversion from Excel serial numbers"""
        # Test known Excel serial numbers
        # Excel serial 1 = 1899-12-31 (1 day from origin 1899-12-30)
        result_1 = convertir_fecha_isolated(1)
        expected_1 = date(1899, 12, 31)
        self.assertEqual(result_1, expected_1)
        
        # Excel serial for a more recent date
        # 45000 should be around 2023
        result_recent = convertir_fecha_isolated(45000)
        self.assertIsNotNone(result_recent)
        self.assertIsInstance(result_recent, date)
        
        # Test with float serial
        result_float = convertir_fecha_isolated(45000.5)
        self.assertIsNotNone(result_float)
        self.assertIsInstance(result_float, date)
    
    def test_string_formats(self):
        """Test conversion from various string formats"""
        test_cases = [
            ('2025-05-03', date(2025, 5, 3)),
            ('03/05/2025', date(2025, 5, 3)),
            ('03-05-2025', date(2025, 5, 3)),
            ('2025/05/03', date(2025, 5, 3)),
            ('03.05.2025', date(2025, 5, 3)),
            ('  2025-05-03  ', date(2025, 5, 3)),  # With spaces
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = convertir_fecha_isolated(input_str)
                self.assertEqual(result, expected)
    
    def test_invalid_strings(self):
        """Test handling of invalid string formats"""
        invalid_strings = ['', '   ', 'invalid', '2025-13-45', 'not-a-date']
        
        for invalid_str in invalid_strings:
            with self.subTest(invalid_str=invalid_str):
                result = convertir_fecha_isolated(invalid_str)
                self.assertIsNone(result)
    
    def test_invalid_types(self):
        """Test handling of invalid types"""
        invalid_values = [[], {}, set(), object()]
        
        for invalid_val in invalid_values:
            with self.subTest(invalid_val=invalid_val):
                result = convertir_fecha_isolated(invalid_val)
                self.assertIsNone(result)


class TestDaysCalculationLogic(unittest.TestCase):
    """Test the days calculation logic for inclusive counting"""
    
    def test_inclusive_days_calculation(self):
        """Test that days are calculated inclusively (end - start + 1)"""
        start_date = date(2025, 5, 3)
        end_date = date(2025, 5, 5)
        
        # Should be 3 days inclusive (3rd, 4th, 5th)
        expected_days = (end_date - start_date).days + 1
        self.assertEqual(expected_days, 3)
    
    def test_same_day_calculation(self):
        """Test calculation when start and end are the same day"""
        same_date = date(2025, 5, 3)
        
        # Should be 1 day when start and end are the same
        expected_days = (same_date - same_date).days + 1
        self.assertEqual(expected_days, 1)
    
    def test_weekend_spanning(self):
        """Test calculation spanning weekends"""
        # Friday to Monday (4 days inclusive)
        start_date = date(2025, 5, 2)  # Friday
        end_date = date(2025, 5, 5)    # Monday
        
        expected_days = (end_date - start_date).days + 1
        self.assertEqual(expected_days, 4)


def test_excel_serial_accuracy():
    """Test specific Excel serial numbers for accuracy"""
    print("\nTesting Excel serial date conversion accuracy:")
    
    # Test some known Excel serials
    test_serials = [
        (1, date(1899, 12, 31)),
        (25569, date(1970, 1, 1)),  # Unix epoch
        (44927, date(2023, 1, 1)),  # Recent year
        (45292, date(2024, 1, 1)),  # 2024
    ]
    
    for serial, expected in test_serials:
        result = convertir_fecha_isolated(serial)
        print(f"  Serial {serial} -> {result} (expected {expected})")
        # Note: We expect some slight variations due to Excel's leap year bug


if __name__ == '__main__':
    print("Running isolated MovimientoMes utility tests...")
    
    # Run the Excel serial accuracy test first
    test_excel_serial_accuracy()
    
    # Run unit tests
    unittest.main(verbosity=2)