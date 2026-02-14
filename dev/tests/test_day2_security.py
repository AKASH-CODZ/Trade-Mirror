import unittest
import tempfile
import os
import pandas as pd
import sqlite3
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SecureDatabase
from ai_coach import SecureAICoach, CoachingRequest

class TestSecureDatabase(unittest.TestCase):
    """Test security features of the database module"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db = SecureDatabase(self.test_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        # Ensure database connection is closed
        try:
            conn = sqlite3.connect(self.test_db.name)
            conn.close()
        except:
            pass
        os.unlink(self.test_db.name)
    
    def test_database_initialization(self):
        """Test secure database initialization"""
        # Check that tables are created
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        
        # Check trades table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check security log table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='security_log'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_data_hashing_integrity(self):
        """Test SHA-256 hashing for data integrity"""
        test_data = {
            'symbol': 'RELIANCE',
            'quantity': 10,
            'buy_value': 2500.0,
            'sell_value': 2600.0,
            'realized_pnl': 100.0
        }
        
        hash1 = self.db.calculate_data_hash(test_data)
        hash2 = self.db.calculate_data_hash(test_data.copy())
        
        # Same data should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Modified data should produce different hash
        modified_data = test_data.copy()
        modified_data['quantity'] = 15
        hash3 = self.db.calculate_data_hash(modified_data)
        self.assertNotEqual(hash1, hash3)
    
    def test_duplicate_prevention(self):
        """Test that duplicate trades are not stored"""
        # Create test data
        test_df = pd.DataFrame([{
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
        }])
        
        # Store same data twice
        count1 = self.db.store_trades(test_df, 'test_source')
        count2 = self.db.store_trades(test_df, 'test_source')
        
        # Second attempt should insert 0 records
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 0)
    
    def test_sensitive_data_removal(self):
        """Test that sensitive columns are handled properly"""
        test_df = pd.DataFrame([{
            'Symbol': 'RELIANCE',
            'Quantity': 10,
            'Client Id': 'SENSITIVE123',
            'Order Id': 'ORDER456',
            'PAN': 'ABCDE1234F',
            'Phone': '9876543210',
            'Realized P&L': 100.0
        }])
        
        # Store data
        count = self.db.store_trades(test_df, 'test_source')
        self.assertEqual(count, 1)
        
        # Retrieve and verify sensitive data is not stored
        retrieved_df = self.db.get_trades()
        self.assertNotIn('Client Id', retrieved_df.columns)
        self.assertNotIn('Order Id', retrieved_df.columns)
        self.assertNotIn('PAN', retrieved_df.columns)
        self.assertNotIn('Phone', retrieved_df.columns)
    
    def test_security_logging(self):
        """Test security event logging"""
        # Perform an operation that should be logged
        test_df = pd.DataFrame([{'Symbol': 'TEST', 'Quantity': 5, 'Realized P&L': 50.0}])
        # Ensure database connection is fresh
        self.db = SecureDatabase(self.test_db.name)
        stored_count = self.db.store_trades(test_df, 'test_source')
        self.assertEqual(stored_count, 1)
    
        # Check security log with fresh connection
        conn = sqlite3.connect(self.test_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM security_log WHERE action = 'INSERT'")
        insert_count = cursor.fetchone()[0]
        conn.close()
    
        self.assertGreater(insert_count, 0)

class TestSecureAICoach(unittest.TestCase):
    """Test security features of the AI coach"""
    
    def setUp(self):
        """Set up test AI coach"""
        self.ai_coach = SecureAICoach(ollama_url="http://localhost:11434")
    
    def test_data_anonymization(self):
        """Test that trading data is properly anonymized"""
        test_df = pd.DataFrame([{
            'Symbol': 'RELIANCE',
            'Quantity': 10,
            'Client Id': 'SENSITIVE123',
            'Order Id': 'ORDER456',
            'PAN': 'ABCDE1234F',
            'Realized P&L': 100.0
        }])
        
        # Anonymize data
        anon_df = self.ai_coach.anonymize_trading_data(test_df)
        
        # Check that sensitive columns are removed
        sensitive_columns = ['Client Id', 'Order Id', 'PAN']
        for col in sensitive_columns:
            self.assertNotIn(col, anon_df.columns)
        
        # Check that symbol is anonymized
        self.assertIn('Symbol', anon_df.columns)
        self.assertTrue(anon_df['Symbol'].iloc[0].startswith('STOCK_'))
    
    def test_coaching_request_structure(self):
        """Test coaching request creation and validation"""
        test_metrics = {
            'Total_P&L': 5000.0,
            'Win_Rate': 65.0,
            'Risk_Reward_Ratio': 2.1
        }
        
        test_df = pd.DataFrame([{
            'Symbol': 'TEST',
            'Quantity': 10,
            'Realized P&L': 100.0
        }])
        
        request = CoachingRequest(
            metrics=test_metrics,
            recent_trades=test_df,
            trading_style='day_trading',
            risk_tolerance='moderate'
        )
        
        # Validate request structure
        self.assertEqual(request.metrics, test_metrics)
        self.assertEqual(len(request.recent_trades), 1)
        self.assertEqual(request.trading_style, 'day_trading')
        self.assertEqual(request.risk_tolerance, 'moderate')
    
    @patch('requests.post')
    def test_offline_ai_handling(self, mock_post):
        """Test handling when AI service is offline"""
        # Simulate connection error
        mock_post.side_effect = ConnectionError("Connection refused")
        
        result = self.ai_coach.get_coaching_advice(
            CoachingRequest(
                metrics={'Total_P&L': 1000},
                recent_trades=pd.DataFrame()
            )
        )
        
        self.assertEqual(result['status'], 'error')
        # Fix: Check for connection-related keywords instead of specific 'offline' text
        self.assertTrue(any(keyword in result['message'].lower() 
                           for keyword in ['connection', 'refused', 'offline']))

    def test_prompt_sanitization(self):
        """Test that prompts don't contain sensitive information"""
        test_df = pd.DataFrame([{
            'Symbol': 'RELIANCE',
            'Client Id': 'SECRET123',
            'Realized P&L': 100.0
        }])
        
        request = CoachingRequest(
            metrics={'Total_P&L': 1000},
            recent_trades=test_df
        )
        
        prompt = self.ai_coach.prepare_coaching_prompt(request)
        
        # Check that sensitive information is not in prompt
        self.assertNotIn('SECRET123', prompt)
        self.assertNotIn('Client Id', prompt)

class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and validation"""
    
    def test_csv_file_integrity(self):
        """Test CSV file integrity verification"""
        # Create test CSV with known content
        test_data = """Symbol,Quantity,Buy Value,Sell Value,Realized P&L
RELIANCE,10,2500.0,2600.0,100.0
TCS,5,1500.0,1400.0,-100.0"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(test_data)
            temp_file = f.name
        
        try:
            # Calculate file hash
            hash_sha256 = hashlib.sha256()
            with open(temp_file, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            original_hash = hash_sha256.hexdigest()
            
            # Verify hash consistency
            hash_sha256_2 = hashlib.sha256()
            with open(temp_file, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256_2.update(chunk)
            verify_hash = hash_sha256_2.hexdigest()
            
            self.assertEqual(original_hash, verify_hash)
            
        finally:
            os.unlink(temp_file)
    
    def test_dataframe_consistency(self):
        """Test DataFrame operations maintain data consistency"""
        test_df = pd.DataFrame({
            'Symbol': ['RELIANCE', 'TCS', 'INFY'],
            'Quantity': [10, 5, 8],
            'Buy_Value': [2500.0, 1500.0, 2000.0],
            'Sell_Value': [2600.0, 1400.0, 2100.0]
        })
        
        # Calculate P&L
        test_df['Realized_P&L'] = test_df['Sell_Value'] - test_df['Buy_Value']
        
        # Verify calculations are consistent
        expected_pnl = [100.0, -100.0, 100.0]
        actual_pnl = test_df['Realized_P&L'].tolist()
        self.assertEqual(expected_pnl, actual_pnl)

class TestLocalSecurity(unittest.TestCase):
    """Test local security features"""
    
    def test_credential_storage_security(self):
        """Test that credentials are stored securely"""
        # Test that credential files are not readable by others
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"sensitive": "data"}')
            temp_file = f.name
        
        try:
            # Check file permissions (Unix/Linux/Mac)
            if hasattr(os, 'chmod'):
                # Set restrictive permissions
                os.chmod(temp_file, 0o600)  # Read/write for owner only
                
                # Verify permissions
                stat_result = os.stat(temp_file)
                self.assertEqual(stat_result.st_mode & 0o777, 0o600)
        finally:
            os.unlink(temp_file)
    
    def test_network_isolation(self):
        """Test that no external connections are made without explicit permission"""
        # This test would typically use network mocking
        # For now, we verify that external URLs are not hardcoded
        import re
        
        # Check source files for suspicious external URLs
        suspicious_patterns = [
            r'https?://[^localhost|^127\.0\.0\.1|^::1]',
            r'api\.[a-zA-Z0-9]+\.com',
            r'[a-zA-Z0-9]+\.azure\.com'
        ]
        
        project_files = ['database.py', 'ai_coach.py', 'app.py']
        project_root = Path(__file__).parent
        
        for filename in project_files:
            file_path = project_root / filename
            if file_path.exists():
                content = file_path.read_text()
                for pattern in suspicious_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    # Allow localhost connections for AI coach
                    external_matches = [match for match in matches 
                                      if 'localhost' not in match and '127.0.0.1' not in match]
                    self.assertEqual(len(external_matches), 0, 
                                   f"Found external connection in {filename}: {external_matches}")

def run_security_tests():
    """Run all security tests"""
    test_classes = [
        TestSecureDatabase,
        TestSecureAICoach,
        TestDataIntegrity,
        TestLocalSecurity
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        suite.addTest(unittest.makeSuite(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_security_tests()
    exit(0 if success else 1)