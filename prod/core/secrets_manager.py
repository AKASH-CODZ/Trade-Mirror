"""
Secrets Manager for TradeMirror Pro
Handles persistent storage of API keys and user preferences
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Manages encrypted storage of sensitive configuration data
    """
    
    def __init__(self):
        # Define secrets file location
        self.project_root = Path(__file__).parent.parent.parent
        self.secrets_file = self.project_root / ".streamlit" / "secrets.json"
        self.key_file = self.project_root / ".streamlit" / "secret.key"
        
        # Create directories if they don't exist
        self.secrets_file.parent.mkdir(exist_ok=True)
        
        # Initialize encryption
        self.cipher_suite = self._initialize_encryption()
    
    def _initialize_encryption(self) -> Fernet:
        """Initialize or load encryption key"""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions
                os.chmod(self.key_file, 0o600)
            
            return Fernet(key)
        except Exception as e:
            logger.error(f"Encryption initialization failed: {e}")
            # Fallback to basic encoding (not recommended for production)
            return None
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if self.cipher_suite:
            try:
                encrypted = self.cipher_suite.encrypt(data.encode())
                return base64.urlsafe_b64encode(encrypted).decode()
            except Exception as e:
                logger.error(f"Encryption failed: {e}")
                return data  # Return unencrypted as fallback
        return data
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if self.cipher_suite and encrypted_data:
            try:
                encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
                decrypted = self.cipher_suite.decrypt(encrypted_bytes)
                return decrypted.decode()
            except Exception as e:
                logger.error(f"Decryption failed: {e}")
                return encrypted_data  # Return as-is as fallback
        return encrypted_data
    
    def save_secret(self, key: str, value: str) -> bool:
        """Save an encrypted secret"""
        try:
            # Load existing secrets
            secrets = self.load_secrets()
            
            # Encrypt the value
            encrypted_value = self._encrypt_data(value)
            secrets[key] = encrypted_value
            
            # Save to file
            with open(self.secrets_file, 'w') as f:
                json.dump(secrets, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.secrets_file, 0o600)
            
            logger.info(f"Secret '{key}' saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save secret '{key}': {e}")
            return False
    
    def get_secret(self, key: str, default: str = "") -> str:
        """Retrieve and decrypt a secret"""
        try:
            secrets = self.load_secrets()
            encrypted_value = secrets.get(key, "")
            
            if encrypted_value:
                return self._decrypt_data(encrypted_value)
            return default
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{key}': {e}")
            return default
    
    def load_secrets(self) -> Dict[str, str]:
        """Load all secrets from file"""
        try:
            if self.secrets_file.exists():
                with open(self.secrets_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            return {}
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        try:
            secrets = self.load_secrets()
            if key in secrets:
                del secrets[key]
                with open(self.secrets_file, 'w') as f:
                    json.dump(secrets, f, indent=2)
                logger.info(f"Secret '{key}' deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete secret '{key}': {e}")
            return False
    
    def list_secrets(self) -> list:
        """List all secret keys (without values)"""
        try:
            secrets = self.load_secrets()
            return list(secrets.keys())
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []

# Global instance
secrets_manager = SecretsManager()

# Convenience functions
def save_api_key(provider: str, api_key: str) -> bool:
    """Save API key for a specific provider"""
    return secrets_manager.save_secret(f"api_key_{provider.lower()}", api_key)

def get_api_key(provider: str, default: str = "") -> str:
    """Get API key for a specific provider"""
    return secrets_manager.get_secret(f"api_key_{provider.lower()}", default)

def save_user_preference(key: str, value: str) -> bool:
    """Save user preference"""
    return secrets_manager.save_secret(f"pref_{key}", value)

def get_user_preference(key: str, default: str = "") -> str:
    """Get user preference"""
    return secrets_manager.get_secret(f"pref_{key}", default)