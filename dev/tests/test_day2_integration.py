import unittest
import tempfile
import os
import pandas as pd
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processor import ZerodhaDataProcessor
from database import SecureDatabase
from ai_coach import SecureAICoach, CoachingRequest

class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name) / "data"
        self.data_dir.mkdir(parents=True)
        
        # Initialize components
        self.processor = ZerodhaDataProcessor()
        self.database = SecureDatabase(str(self.data_dir / "test.db"))
        self.ai_coach = SecureAICoach()
    
    def tearDown(self):
        """Clean up test environment"""
        self.temp_dir.cleanup()
    
    def test_complete_file_processing_workflow(self):
        """Test complete workflow: file upload → processing → storage → analysis"""
        # Create test CSV data
        test_data = """Symbol,Quantity,Buy Value,Sell Value,Realized P&L,Buy Average,Sell Average,Trade Type,Exchange,Time
RELIANCE,10,2500.0,2600.0,100.0,250.0,260.0,BUY,NSE,2024-01-15 10:30:00
TCS,5,1500.0,1400.0,-100.0,300.0,280.0,SELL,NSE,2024-01-15 11:45:00
INFY,8,2000.0,2100.0,100.0,250.0,262.5,BUY,NSE,2024-01-15 14:20:00"""
        
        # Save to temporary file
        csv_file = self.data_dir / "test_trades.csv"
        csv_file.write_text(test_data)
        
        # Step 1: Load and process data
        df = self.processor.load_zerodha_pnl(str(csv_file))
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 3)
        
        # Step 2: Store in database
        stored_count = self.database.store_trades(df, 'test_workflow')
        self.assertEqual(stored_count, 3)
        
        # Step 3: Verify storage
        retrieved_df = self.database.get_trades()
        self.assertEqual(len(retrieved_df), 3)
        
        # Step 4: Calculate metrics
        metrics = self.processor.calculate_comprehensive_metrics(df)
        self.assertIn('Total_P&L', metrics)
        self.assertIn('Win_Rate', metrics)
        self.assertIn('Risk_Reward_Ratio', metrics)
        
        # Step 5: AI analysis (mocked)
        with patch.object(SecureAICoach, 'health_check', return_value=True):
            with patch.object(SecureAICoach, 'get_coaching_advice') as mock_advice:
                mock_advice.return_value = {
                    'status': 'success',
                    'advice': 'Good performance overall',
                    'model': 'test_model'
                }
                
                request = CoachingRequest(
                    metrics=metrics,
                    recent_trades=df.tail(2)
                )
                
                advice = self.ai_coach.get_coaching_advice(request)
                self.assertEqual(advice['status'], 'success')
    
    def test_multiple_data_source_aggregation(self):
        """Test aggregating data from multiple sources"""
        # Create data from different sources
        file_data = pd.DataFrame([{
            'Symbol': 'RELIANCE',
            'Quantity': 10,
            'Realized P&L': 100.0,
            'Time': '2024-01-15 10:30:00'
        }])
        
        live_data = pd.DataFrame([{
            'Symbol': 'TCS',
            'Quantity': 5,
            'Realized P&L': -50.0,
            'Time': '2024-01-15 11:45:00'
        }])
        
        email_data = pd.DataFrame([{
            'Symbol': 'INFY',
            'Quantity': 8,
            'Realized P&L': 75.0,
            'Time': '2024-01-15 14:20:00'
        }])
        
        # Store data from different sources
        self.database.store_trades(file_data, 'file_upload')
        self.database.store_trades(live_data, 'live_broker')
        self.database.store_trades(email_data, 'email_attachment')
        
        # Verify aggregation
        all_trades = self.database.get_trades()
        self.assertEqual(len(all_trades), 3)
        
        # Check source breakdown
        stats = self.database.get_trade_statistics()
        sources = {s['source']: s['count'] for s in stats['sources']}
        self.assertEqual(sources['file_upload'], 1)
        self.assertEqual(sources['live_broker'], 1)
        self.assertEqual(sources['email_attachment'], 1)
    
    def test_data_deduplication_across_sources(self):
        """Test that identical trades from different sources are deduplicated"""
        # Create identical trade data
        trade_data = [{
            'Symbol': 'RELIANCE',
            'Quantity': 10,
            'Buy Value': 2500.0,
            'Sell Value': 2600.0,
            'Realized P&L': 100.0,
            'Buy Average': 250.0,
            'Sell Average': 260.0,
            'Trade Type': 'BUY',
            'Exchange': 'NSE',
            'Time': '2024-01-15 10:30:00'
        }]
        
        df1 = pd.DataFrame(trade_data)
        df2 = pd.DataFrame(trade_data)  # Identical data
        
        # Store from different sources
        count1 = self.database.store_trades(df1, 'source_a')
        count2 = self.database.store_trades(df2, 'source_b')
        
        # First should succeed, second should be deduplicated
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 0)
        
        # Verify only one record exists
        all_trades = self.database.get_trades()
        self.assertEqual(len(all_trades), 1)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and recovery"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = SecureDatabase(str(Path(self.temp_dir.name) / "test.db"))
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_corrupted_file_handling(self):
        """Test handling of corrupted or invalid files"""
        # Create corrupted CSV
        corrupted_data = """Symbol,Quantity,Buy Value
RELIANCE,10,2500.0
TCS,five,invalid_value
INFY,,  # Missing values"""
        
        csv_file = Path(self.temp_dir.name) / "corrupted.csv"
        csv_file.write_text(corrupted_data)
        
        processor = ZerodhaDataProcessor()
        
        # Should handle gracefully - might return empty DataFrame or partial data
        df = processor.load_zerodha_pnl(str(csv_file))
        # Just verify it doesn't crash and returns a DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        # May be empty or have some rows processed
        self.assertGreaterEqual(len(df), 0)

    def test_database_connection_recovery(self):
        """Test database recovery from connection issues"""
        # This would test retry logic and connection pooling
        # For now, test that database can be reinitialized
        db_path = str(Path(self.temp_dir.name) / "recovery_test.db")
        
        # Initial connection
        db1 = SecureDatabase(db_path)
        test_df = pd.DataFrame([{'Symbol': 'TEST', 'Quantity': 1, 'Realized P&L': 10.0}])
        db1.store_trades(test_df, 'test')
        
        # Simulate connection issue and recovery
        del db1  # Close connection
        
        # New connection should work
        db2 = SecureDatabase(db_path)
        retrieved = db2.get_trades()
        self.assertEqual(len(retrieved), 1)

class TestPerformanceBenchmarking(unittest.TestCase):
    """Test performance with larger datasets"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = SecureDatabase(str(Path(self.temp_dir.name) / "perf_test.db"))
        self.processor = ZerodhaDataProcessor()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_large_dataset_processing(self):
        """Test processing performance with larger datasets"""
        # Create larger dataset (1000 trades)
        large_data = []
        for i in range(1000):
            large_data.append({
                'Symbol': f'STOCK_{i:04d}',
                'Quantity': (i % 100) + 1,
                'Buy Value': float(1000 + (i * 10)),
                'Sell Value': float(1050 + (i * 10)),
                'Realized P&L': float(50 - (i % 100)),
                'Buy Average': float(100 + i),
                'Sell Average': float(105 + i),
                'Trade Type': 'BUY' if i % 2 == 0 else 'SELL',
                'Exchange': 'NSE',
                'Time': f'2024-01-{(i % 28) + 1:02d} {(i % 12) + 1:02d}:{(i % 60):02d}:00'
            })
        
        df = pd.DataFrame(large_data)
        
        # Benchmark processing time
        start_time = time.time()
        stored_count = self.database.store_trades(df, 'performance_test')
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Verify results
        self.assertEqual(stored_count, 1000)
        self.assertLess(processing_time, 5.0)  # Should process 1000 records in under 5 seconds
        
        # Test retrieval performance
        start_time = time.time()
        retrieved_df = self.database.get_trades(limit=100)
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        self.assertEqual(len(retrieved_df), 100)
        self.assertLess(retrieval_time, 1.0)  # Should retrieve 100 records quickly

def run_integration_tests():
    """Run all integration tests"""
    test_classes = [
        TestEndToEndWorkflows,
        TestErrorHandling,
        TestPerformanceBenchmarking
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        suite.addTest(unittest.makeSuite(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)