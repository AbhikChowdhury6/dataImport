import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import shutil
from rwWorkingTSDf import (
    writeWorkingTSDf,
    readWorkingTSDF,
    short_hash_df,
    fnString_to_dt,
    dt_to_fnString,
    calcRowsPerFile
)

class TestRWWorkingTSDf(unittest.TestCase):
    def setUp(self):
        """Set up test data and directories"""
        # Create test directory
        self.test_dir = "test_working_data/"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        # Create sample time series data
        dates = pd.date_range(
            start='2024-01-01', 
            end='2024-01-02', 
            freq='1min',
            tz='UTC'
        )
        self.test_df = pd.DataFrame(
            {'value': np.random.randn(len(dates))}, 
            index=dates
        )
        
        # Test parameters
        self.responsible_party = "test_company"
        self.instance = "test_instance"
        self.developing_party = "test_dev"
        self.device = "test_device"
        self.data_type = "test_type"
        self.data_source = "test_source"

    def tearDown(self):
        """Clean up test directories"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_short_hash_df(self):
        """Test the short hash function"""
        # Test same dataframe produces same hash
        hash1 = short_hash_df(self.test_df)
        hash2 = short_hash_df(self.test_df)
        self.assertEqual(hash1, hash2)
        
        # Test different dataframes produce different hashes
        different_df = self.test_df.copy()
        different_df['value'] = different_df['value'] + 1
        different_hash = short_hash_df(different_df)
        self.assertNotEqual(hash1, different_hash)

    def test_datetime_conversion(self):
        """Test datetime to filename string conversion"""
        test_dt = datetime(2024, 1, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
        fn_string = dt_to_fnString(test_dt)
        converted_dt = fnString_to_dt(fn_string)
        self.assertEqual(test_dt, converted_dt)

    def test_write_and_read_basic(self):
        """Test basic write and read functionality"""
        # Write test data
        writeWorkingTSDf(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source,
            self.test_df,
            targetFileSize=1024 * 1024  # 1MB for testing
        )
        
        # Read back the data
        read_df = readWorkingTSDF(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source
        )
        
        # Verify data integrity
        pd.testing.assert_frame_equal(self.test_df, read_df)

    def test_timezone_conversion(self):
        """Test timezone conversion during read"""
        # Write in UTC
        writeWorkingTSDf(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source,
            self.test_df
        )
        
        # Read with different timezone
        read_df = readWorkingTSDF(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source,
            chnageTz="America/New_York"
        )
        
        self.assertEqual(str(read_df.index.tz), "America/New_York")

    def test_date_range_filter(self):
        """Test reading specific date ranges"""
        writeWorkingTSDf(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source,
            self.test_df
        )
        
        start_time = self.test_df.index[10]
        end_time = self.test_df.index[20]
        
        filtered_df = readWorkingTSDF(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source,
            startTime=start_time,
            endTime=end_time
        )
        
        self.assertEqual(len(filtered_df), 11)  # Including both start and end
        self.assertTrue((filtered_df.index >= start_time).all())
        self.assertTrue((filtered_df.index <= end_time).all())

    def test_file_size_calculation(self):
        """Test the file size calculation functionality"""
        rows = calcRowsPerFile(
            self.test_df,
            targetFileSize=1024 * 1024,  # 1MB
            targetPath=self.test_dir
        )
        self.assertGreater(rows, 0)

    def test_empty_dataframe(self):
        """Test handling of empty dataframes"""
        empty_df = pd.DataFrame(columns=['value'])
        empty_df.index = pd.DatetimeIndex([], tz='UTC')
        
        writeWorkingTSDf(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source,
            empty_df
        )
        
        result = readWorkingTSDF(
            self.responsible_party,
            self.instance,
            self.developing_party,
            self.device,
            self.data_type,
            self.data_source
        )
        
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 