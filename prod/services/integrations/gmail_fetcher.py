import os
import base64
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logging.warning("Google API not available. Install with: pip install google-auth google-auth-oauthlib google-api-python-client")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureGmailConnector:
    """
    Secure Gmail connector for fetching trading reports with zero-trust security model.
    All credentials and data remain local - nothing leaves your machine.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    TOKEN_FILE = 'data/token.json'
    CREDENTIALS_FILE = 'data/credentials.json'
    
    def __init__(self, download_dir: str = "data/downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.creds = None
        
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries not installed")
            
        self._authenticate()
    
    def _authenticate(self) -> bool:
        """Handle OAuth2 authentication with local credential storage"""
        try:
            # Load existing token
            if os.path.exists(self.TOKEN_FILE):
                self.creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
            
            # Refresh or get new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # Check for credentials file
                    if not os.path.exists(self.CREDENTIALS_FILE):
                        raise FileNotFoundError(
                            f"Credentials file not found at {self.CREDENTIALS_FILE}. "
                            "Please download credentials.json from Google Cloud Console."
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.CREDENTIALS_FILE, self.SCOPES
                    )
                    # Local server authentication - opens browser on your machine
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials securely
                with open(self.TOKEN_FILE, 'w') as token:
                    token.write(self.creds.to_json())
                
                logger.info("Authentication successful - credentials stored locally")
            
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of downloaded file for integrity verification"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def fetch_trading_reports(self, sender_domains: List[str] = None, 
                            file_types: List[str] = None, 
                            limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch trading reports from specified senders with security validation.
        
        Args:
            sender_domains: List of trusted domains (default: ['zerodha.com', 'upstox.com'])
            file_types: List of acceptable file extensions (default: ['.csv', '.xlsx', '.pdf'])
            limit: Maximum number of emails to process
            
        Returns:
            List of dictionaries containing file information and metadata
        """
        if sender_domains is None:
            sender_domains = ['zerodha.com', 'upstox.com', 'groww.in', 'aliceblue.com']
        
        if file_types is None:
            file_types = ['.csv', '.xlsx', '.xls', '.pdf']
        
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            
            # Build search query
            domain_queries = [f"from:{domain}" for domain in sender_domains]
            search_query = f"({' OR '.join(domain_queries)}) has:attachment"
            
            logger.info(f"Searching for emails with query: {search_query}")
            
            # Search for messages
            results = service.users().messages().list(
                userId='me', 
                q=search_query, 
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            downloaded_files = []
            
            logger.info(f"Found {len(messages)} potential trading report emails")
            
            for msg in messages:
                try:
                    # Get message details
                    message = service.users().messages().get(
                        userId='me', 
                        id=msg['id']
                    ).execute()
                    
                    # Extract email metadata
                    headers = message['payload']['headers']
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    logger.info(f"Processing email: {subject} from {sender}")
                    
                    # Process attachments
                    if 'parts' in message['payload']:
                        for part in message['payload']['parts']:
                            if 'filename' in part and part['filename']:
                                attachment_info = self._process_attachment(
                                    service, msg['id'], part, subject, sender
                                )
                                
                                if attachment_info:
                                    # Validate file type
                                    file_ext = Path(attachment_info['filename']).suffix.lower()
                                    if file_ext in file_types:
                                        downloaded_files.append(attachment_info)
                                        logger.info(f"✅ Downloaded: {attachment_info['filename']}")
                                    else:
                                        logger.debug(f"Skipping unsupported file type: {file_ext}")
                
                except Exception as e:
                    logger.error(f"Error processing message {msg['id']}: {str(e)}")
                    continue
            
            logger.info(f"Successfully downloaded {len(downloaded_files)} trading reports")
            return downloaded_files
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch trading reports: {str(e)}")
            raise
    
    def _process_attachment(self, service, message_id: str, part: Dict, 
                          subject: str, sender: str) -> Optional[Dict[str, Any]]:
        """Process individual attachment with security validation"""
        try:
            filename = part['filename']
            
            # Get attachment data
            if 'data' in part['body']:
                data = part['body']['data']
            else:
                att_id = part['body']['attachmentId']
                attachment = service.users().messages().attachments().get(
                    userId='me', 
                    messageId=message_id, 
                    id=att_id
                ).execute()
                data = attachment['data']
            
            # Decode attachment
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            
            # Create safe filename
            safe_filename = self._create_safe_filename(filename, subject)
            file_path = self.download_dir / safe_filename
            
            # Write file with atomic operation
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            with open(temp_path, 'wb') as f:
                f.write(file_data)
            
            # Calculate integrity hash
            file_hash = self._calculate_file_hash(temp_path)
            
            # Atomic move
            temp_path.rename(file_path)
            
            return {
                'filename': safe_filename,
                'original_filename': filename,
                'full_path': str(file_path),
                'size_bytes': len(file_data),
                'sha256_hash': file_hash,
                'email_subject': subject,
                'email_sender': sender,
                'download_timestamp': datetime.now().isoformat(),
                'message_id': message_id
            }
            
        except Exception as e:
            logger.error(f"Failed to process attachment {part.get('filename', 'unknown')}: {str(e)}")
            return None
    
    def _create_safe_filename(self, original_filename: str, email_subject: str) -> str:
        """Create safe filename with timestamp to prevent collisions"""
        # Remove unsafe characters
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_")
        safe_name = ''.join(c if c in safe_chars else '_' for c in original_filename)
        
        # Add timestamp and email context
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subject_snippet = email_subject[:30].replace(' ', '_').replace(':', '').replace('/', '_')
        
        # Combine with extension
        ext = Path(safe_name).suffix
        stem = Path(safe_name).stem
        
        return f"{timestamp}_{subject_snippet}_{stem}{ext}"
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get statistics about downloaded files"""
        try:
            files = list(self.download_dir.glob('*'))
            
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            file_types = {}
            
            for f in files:
                if f.is_file():
                    ext = f.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            return {
                'total_files': len(files),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': file_types,
                'download_directory': str(self.download_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get download statistics: {str(e)}")
            return {}

# Backward compatibility function
def get_gmail_connector(download_dir: str = "data/downloads") -> SecureGmailConnector:
    """Get Gmail connector instance"""
    return SecureGmailConnector(download_dir)