"""
Test suite for Day 5 Control Center functionality
Tests the new UI architecture, secrets management, and AI provider switching
"""

import sys
import os
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "prod" / "core"))

from ai_coach import AIHandler
from secrets_manager import SecretsManager

class TestControlCenter(unittest.TestCase):
    """Test Control Center functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        
        # Create .streamlit directory structure
        streamlit_dir = Path(".streamlit")
        streamlit_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        self.temp_dir.cleanup()
    
    def test_ai_handler_initialization(self):
        """Test AI handler initialization"""
        handler = AIHandler()
        self.assertEqual(handler.base_url_local, "http://localhost:11434/api/generate")
        self.assertEqual(handler.default_model, "llama3")
    
    def test_local_ai_mode(self):
        """Test local AI mode functionality"""
        handler = AIHandler()
        
        # Test with mock response
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'response': 'Test analysis result'}
            mock_post.return_value = mock_response
            
            result = handler.get_analysis(
                "Test prompt", 
                provider="Local (Ollama)"
            )
            
            self.assertEqual(result, "Test analysis result")
            mock_post.assert_called_once()
    
    def test_local_ai_connection_error(self):
        """Test local AI connection error handling"""
        handler = AIHandler()
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("Connection refused")
            
            result = handler.get_analysis(
                "Test prompt",
                provider="Local (Ollama)"
            )
            
            self.assertIn("Connection refused", result)
    
    @patch('builtins.__import__')
    def test_cloud_ai_mode_with_groq(self, mock_import):
        """Test cloud AI mode with Groq available"""
        # Mock Groq import
        mock_groq_module = MagicMock()
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = "Cloud analysis result"
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq_module.Groq.return_value = mock_client
        
        mock_import.return_value = mock_groq_module
        
        handler = AIHandler()
        
        result = handler.get_analysis(
            "Test prompt",
            provider="Cloud (Groq)",
            api_key="test_key_123"
        )
        
        self.assertEqual(result, "Cloud analysis result")
        mock_client.chat.completions.create.assert_called_once()
    
    def test_cloud_ai_missing_key(self):
        """Test cloud AI with missing API key"""
        handler = AIHandler()
        
        result = handler.get_analysis(
            "Test prompt",
            provider="Cloud (Groq)"
        )
        
        self.assertIn("API Key is missing", result)
    
    def test_invalid_provider(self):
        """Test handling of invalid provider"""
        handler = AIHandler()
        
        result = handler.get_analysis(
            "Test prompt",
            provider="Invalid Provider"
        )
        
        self.assertIn("Unknown provider", result)
    
    def test_secrets_manager_initialization(self):
        """Test secrets manager initialization"""
        manager = SecretsManager()
        
        # Check that directories are created
        self.assertTrue(Path(".streamlit").exists())
        self.assertTrue(manager.secrets_file.parent.exists())
    
    def test_secret_storage_and_retrieval(self):
        """Test saving and retrieving secrets"""
        manager = SecretsManager()
        
        # Test saving a secret
        result = manager.save_secret("test_key", "test_value")
        self.assertTrue(result)
        
        # Test retrieving the secret
        retrieved = manager.get_secret("test_key")
        self.assertEqual(retrieved, "test_value")
        
        # Test retrieving non-existent secret
        default_value = manager.get_secret("nonexistent", "default")
        self.assertEqual(default_value, "default")
    
    def test_api_key_convenience_functions(self):
        """Test API key convenience functions"""
        from secrets_manager import save_api_key, get_api_key
        
        # Save API key
        result = save_api_key("groq", "test_api_key_123")
        self.assertTrue(result)
        
        # Retrieve API key
        retrieved = get_api_key("groq")
        self.assertEqual(retrieved, "test_api_key_123")
        
        # Test default value
        default_key = get_api_key("openai", "default_key")
        self.assertEqual(default_key, "default_key")
    
    def test_secrets_encryption(self):
        """Test that secrets are encrypted when stored"""
        manager = SecretsManager()
        
        # Save a secret
        manager.save_secret("sensitive_data", "very_secret_value")
        
        # Check that the stored value is encrypted (not plain text)
        if manager.secrets_file.exists():
            with open(manager.secrets_file, 'r') as f:
                secrets_data = json.load(f)
            
            stored_value = secrets_data.get("sensitive_data", "")
            # The stored value should not be the plain text
            self.assertNotEqual(stored_value, "very_secret_value")
            # But retrieval should still work
            retrieved = manager.get_secret("sensitive_data")
            self.assertEqual(retrieved, "very_secret_value")

if __name__ == '__main__':
    unittest.main()