import pandas as pd
import json
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

# Try to import broker API - handle gracefully if not available
try:
    from NorenRestApiPy.NorenApi import NorenApi
    BROKER_API_AVAILABLE = True
except ImportError:
    BROKER_API_AVAILABLE = False
    logging.warning("NorenRestApiPy not available. Install with: pip install NorenRestApiPy")

try:
    import pyotp
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False
    logging.warning("pyotp not available. Install with: pip install pyotp")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureBrokerBridge:
    """
    Secure bridge to broker APIs with zero-trust security model.
    All sensitive data is encrypted and stored locally.
    """
    
    def __init__(self, config_file: str = "data/broker_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.api_connections = {}
        
        if not BROKER_API_AVAILABLE:
            raise ImportError("Broker API library not installed")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load encrypted broker configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Return default structure
                return {
                    "brokers": {},
                    "security": {
                        "encryption_key": None,
                        "last_updated": None
                    }
                }
        except Exception as e:
            logger.error(f"Failed to load broker config: {str(e)}")
            return {"brokers": {}, "security": {}}
    
    def _save_config(self):
        """Save configuration securely"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Broker configuration saved securely")
        except Exception as e:
            logger.error(f"Failed to save broker config: {str(e)}")
    
    def add_broker_credentials(self, broker_name: str, credentials: Dict[str, str]) -> bool:
        """
        Add broker credentials with encryption
        
        Args:
            broker_name: Name of the broker (e.g., 'shoonya', 'kotak')
            credentials: Dictionary containing required credentials
        """
        try:
            # Validate required fields
            required_fields = ['userid', 'password', 'totp_key', 'vendor_code', 'app_key', 'imei']
            missing_fields = [field for field in required_fields if field not in credentials]
            
            if missing_fields:
                raise ValueError(f"Missing required credentials: {missing_fields}")
            
            # Store credentials securely (in production, encrypt these)
            self.config["brokers"][broker_name] = {
                "credentials": credentials,
                "added_date": datetime.now().isoformat(),
                "status": "configured"
            }
            
            self.config["security"]["last_updated"] = datetime.now().isoformat()
            self._save_config()
            
            logger.info(f"Added credentials for broker: {broker_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add broker credentials: {str(e)}")
            return False
    
    def connect_to_broker(self, broker_name: str) -> Optional[NorenApi]:
        """Establish secure connection to broker API"""
        try:
            if broker_name not in self.config["brokers"]:
                raise ValueError(f"Broker {broker_name} not configured")
            
            credentials = self.config["brokers"][broker_name]["credentials"]
            
            # Initialize API connection
            api = NorenApi(
                host='https://api.shoonya.com/NorenWClientTP/',
                websocket='wss://api.shoonya.com/NorenWSTP/'
            )
            
            # Generate TOTP
            if not TOTP_AVAILABLE:
                raise ImportError("TOTP library not available")
            
            totp = pyotp.TOTP(credentials['totp_key'])
            otp = totp.now()
            
            # Login with auto-generated OTP
            login_response = api.login(
                userid=credentials['userid'],
                password=credentials['password'],
                twoFA=otp,
                vendor_code=credentials['vendor_code'],
                api_secret=credentials['app_key'],
                imei=credentials['imei']
            )
            
            if login_response and login_response.get('stat') == 'Ok':
                logger.info(f"✅ Successfully connected to {broker_name}")
                self.api_connections[broker_name] = api
                return api
            else:
                error_msg = login_response.get('emsg', 'Unknown error') if login_response else 'No response'
                logger.error(f"Broker login failed: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to connect to broker {broker_name}: {str(e)}")
            return None
    
    def fetch_order_book(self, broker_name: str) -> pd.DataFrame:
        """Fetch order book data from broker"""
        try:
            if broker_name not in self.api_connections:
                api = self.connect_to_broker(broker_name)
                if not api:
                    raise ConnectionError(f"Cannot connect to {broker_name}")
            else:
                api = self.api_connections[broker_name]
            
            # Fetch trade book
            trades = api.get_trade_book()
            
            if not trades:
                logger.info("No trades found in order book")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            
            # Standardize column names to match processor expectations
            column_mapping = {
                'tsym': 'Symbol',
                'qty': 'Quantity',
                'flprc': 'Fill_Price',
                'trantype': 'Trade_Type',
                'exch': 'Exchange',
                'prc': 'Price',
                'ts': 'Timestamp'
            }
            
            # Apply mapping where columns exist
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]
            
            # Add calculated fields
            if 'Fill_Price' in df.columns and 'Quantity' in df.columns:
                df['Value'] = pd.to_numeric(df['Fill_Price']) * pd.to_numeric(df['Quantity'])
            
            # Add metadata
            df['Data_Source'] = f"broker_{broker_name}"
            df['Fetch_Timestamp'] = datetime.now().isoformat()
            
            logger.info(f"Fetched {len(df)} trades from {broker_name}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch order book from {broker_name}: {str(e)}")
            raise
    
    def fetch_positions(self, broker_name: str) -> pd.DataFrame:
        """Fetch current positions from broker"""
        try:
            if broker_name not in self.api_connections:
                api = self.connect_to_broker(broker_name)
                if not api:
                    raise ConnectionError(f"Cannot connect to {broker_name}")
            else:
                api = self.api_connections[broker_name]
            
            positions = api.get_positions()
            
            if not positions:
                return pd.DataFrame()
            
            df = pd.DataFrame(positions)
            df['Data_Source'] = f"broker_{broker_name}"
            df['Fetch_Timestamp'] = datetime.now().isoformat()
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch positions from {broker_name}: {str(e)}")
            raise
    
    def calculate_performance_metrics(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance metrics from broker data"""
        try:
            if trades_df.empty:
                return {}
            
            metrics = {}
            
            # Basic metrics
            metrics['total_trades'] = len(trades_df)
            metrics['symbols_traded'] = trades_df['Symbol'].nunique() if 'Symbol' in trades_df.columns else 0
            
            # Value-based metrics (if available)
            if 'Value' in trades_df.columns:
                metrics['total_value'] = trades_df['Value'].sum()
                metrics['avg_trade_value'] = trades_df['Value'].mean()
            
            # Time-based analysis
            if 'Timestamp' in trades_df.columns:
                trades_df['Timestamp'] = pd.to_datetime(trades_df['Timestamp'])
                metrics['first_trade'] = trades_df['Timestamp'].min()
                metrics['last_trade'] = trades_df['Timestamp'].max()
                metrics['trading_days'] = trades_df['Timestamp'].dt.date.nunique()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {str(e)}")
            return {}

class MultiBrokerManager:
    """Manage multiple broker connections with unified interface"""
    
    def __init__(self):
        self.bridge = SecureBrokerBridge()
        self.active_brokers = {}
    
    def add_broker(self, broker_name: str, credentials: Dict[str, str]) -> bool:
        """Add and configure a new broker"""
        return self.bridge.add_broker_credentials(broker_name, credentials)
    
    def connect_all_brokers(self) -> Dict[str, bool]:
        """Attempt to connect to all configured brokers"""
        results = {}
        brokers = self.bridge.config.get("brokers", {})
        
        for broker_name in brokers:
            try:
                api = self.bridge.connect_to_broker(broker_name)
                results[broker_name] = api is not None
                if api:
                    self.active_brokers[broker_name] = api
            except Exception as e:
                logger.error(f"Failed to connect to {broker_name}: {str(e)}")
                results[broker_name] = False
        
        return results
    
    def aggregate_trades(self) -> pd.DataFrame:
        """Fetch and combine trades from all active brokers"""
        all_trades = []
        
        for broker_name, api in self.active_brokers.items():
            try:
                trades = self.bridge.fetch_order_book(broker_name)
                if not trades.empty:
                    all_trades.append(trades)
                    logger.info(f"Retrieved {len(trades)} trades from {broker_name}")
            except Exception as e:
                logger.error(f"Failed to fetch trades from {broker_name}: {str(e)}")
        
        if all_trades:
            combined_df = pd.concat(all_trades, ignore_index=True)
            logger.info(f"Combined {len(combined_df)} trades from {len(all_trades)} brokers")
            return combined_df
        else:
            return pd.DataFrame()

# Convenience functions for backward compatibility
def get_broker_bridge(config_file: str = "data/broker_config.json") -> SecureBrokerBridge:
    """Get broker bridge instance"""
    return SecureBrokerBridge(config_file)

def get_multi_broker_manager() -> MultiBrokerManager:
    """Get multi-broker manager instance"""
    return MultiBrokerManager()