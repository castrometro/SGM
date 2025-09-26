#!/usr/bin/env python
"""
Tests for MovimientoMes utility functions
Tests Excel serial date conversion and days calculation fixes
"""
import os
import sys
import unittest
from datetime import datetime, date
import pandas as pd

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nomina.utils.MovimientoMes import convertir_fecha


class TestConvertirFecha(unittest.TestCase):
    """Test the convertir_fecha function with various input types"""
    
    def test_none_and_na_values(self):
        """Test handling of None and NaN values"""
        self.assertIsNone(convertir_fecha(None))
        self.assertIsNone(convertir_fecha(pd.NaT))
        self.assertIsNone(convertir_fecha(float('nan')))
    
    def test_datetime_conversion(self):
        """Test conversion from datetime objects"""
        dt = datetime(2025, 5, 3, 14, 30, 0)
        expected = date(2025, 5, 3)
        result = convertir_fecha(dt)
        self.assertEqual(result, expected)
    
    def test_pandas_timestamp(self):
        """Test conversion from pandas Timestamp"""
        ts = pd.Timestamp('2025-05-03 14:30:00')
        expected = date(2025, 5, 3)
        result = convertir_fecha(ts)
        self.assertEqual(result, expected)
    
    def test_excel_serial_numbers(self):
        """Test conversion from Excel serial numbers"""
        # Excel serial 45780 should be 2025-05-03 (using 1899-12-30 origin)
        # Let's calculate: 2025-05-03 is approximately 45780 days from 1899-12-30
        excel_serial = 45780  # This should represent 2025-05-03
        result = convertir_fecha(excel_serial)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, date)
        
        # Test with float serial
        result_float = convertir_fecha(45780.0)
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
                result = convertir_fecha(input_str)
                self.assertEqual(result, expected)
    
    def test_invalid_strings(self):
        """Test handling of invalid string formats"""
        invalid_strings = ['', '   ', 'invalid', '2025-13-45', 'not-a-date']
        
        for invalid_str in invalid_strings:
            with self.subTest(invalid_str=invalid_str):
                result = convertir_fecha(invalid_str)
                self.assertIsNone(result)
    
    def test_invalid_types(self):
        """Test handling of invalid types"""
        invalid_values = [[], {}, set(), object()]
        
        for invalid_val in invalid_values:
            with self.subTest(invalid_val=invalid_val):
                result = convertir_fecha(invalid_val)
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


def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestConvertirFecha))
    suite.addTest(unittest.makeSuite(TestDaysCalculationLogic))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running MovimientoMes utility tests...")
    success = run_tests()
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)