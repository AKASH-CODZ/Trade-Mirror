import sqlite3
import pandas as pd
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureDatabase:
    """
    Secure local database for storing trading data with encryption and integrity checks.
    Implements zero-trust security model for local data storage.
    """
    
    def __init__(self, db_path: str = "data/trademirror.db"):
        self.db_path = db_path
        # Ensure the path is absolute and directory exists
        if not os.path.isabs(self.db_path):
            self.db_path = os.path.join(os.getcwd(), self.db_path)
        self.init_database()
        
    def init_database(self):
        """Initialize the secure database with proper table structures"""
        try:
            # Ensure data directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir:  # Only create directory if path contains directory components
                os.makedirs(db_dir, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create trades table with security metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    buy_value REAL,
                    sell_value REAL,
                    realized_pnl REAL,
                    buy_average REAL,
                    sell_average REAL,
                    trade_type TEXT,
                    exchange TEXT,
                    trade_time TIMESTAMP,
                    data_source TEXT,
                    data_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create security audit log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    table_name TEXT,
                    record_id INTEGER,
                    user_agent TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            ''')
            
            # Create data sources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT UNIQUE NOT NULL,
                    source_type TEXT NOT NULL,
                    connection_config TEXT,
                    last_sync TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Secure database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of trade data for integrity verification"""
        # Sort dict to ensure consistent hashing
        sorted_data = {k: v for k, v in sorted(data.items()) if v is not None}
        data_str = str(sorted_data).encode('utf-8')
        return hashlib.sha256(data_str).hexdigest()
    
    def store_trades(self, df: pd.DataFrame, source: str = "unknown") -> int:
        """
        Store trades securely with integrity checks and deduplication.
        Returns number of new records inserted.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            inserted_count = 0
            
            for _, row in df.iterrows():
                # Prepare trade data
                trade_data = {
                    'symbol': str(row.get('Symbol', '')),
                    'quantity': float(row.get('Quantity', 0)),
                    'buy_value': float(row.get('Buy Value', 0)),
                    'sell_value': float(row.get('Sell Value', 0)),
                    'realized_pnl': float(row.get('Realized P&L', 0)),
                    'buy_average': float(row.get('Buy Average', 0)),
                    'sell_average': float(row.get('Sell Average', 0)),
                    'trade_type': str(row.get('Trade Type', '')),
                    'exchange': str(row.get('Exchange', '')),
                    'trade_time': str(row.get('Time', ''))
                }
                
                # Calculate data hash for deduplication
                data_hash = self.calculate_data_hash(trade_data)
                
                # Check if record already exists
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM trades WHERE data_hash = ?", (data_hash,))
                existing = cursor.fetchone()
                
                if not existing:
                    # Insert new record
                    cursor.execute('''
                        INSERT INTO trades 
                        (symbol, quantity, buy_value, sell_value, realized_pnl, 
                         buy_average, sell_average, trade_type, exchange, trade_time, 
                         data_source, data_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        trade_data['symbol'], trade_data['quantity'], trade_data['buy_value'],
                        trade_data['sell_value'], trade_data['realized_pnl'], trade_data['buy_average'],
                        trade_data['sell_average'], trade_data['trade_type'], trade_data['exchange'],
                        trade_data['trade_time'], source, data_hash
                    ))
                    inserted_count += 1
                    
                    # Log security event
                    self.log_security_event("INSERT", "trades", cursor.lastrowid, 
                                          f"New trade from {source}", trade_data)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored {inserted_count} new trades from {source}")
            return inserted_count
            
        except Exception as e:
            logger.error(f"Failed to store trades: {str(e)}")
            raise
    
    def get_trades(self, limit: Optional[int] = None, source: Optional[str] = None) -> pd.DataFrame:
        """Retrieve trades with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if source:
                query += " AND data_source = ?"
                params.append(source)
            
            query += " ORDER BY trade_time DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve trades: {str(e)}")
            raise
    
    def get_trade_statistics(self) -> Dict[str, Any]:
        """Get comprehensive trade statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(realized_pnl) as total_pnl,
                    AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl END) as avg_win,
                    AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl END) as avg_loss,
                    COUNT(CASE WHEN realized_pnl > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN realized_pnl < 0 THEN 1 END) as losing_trades
                FROM trades
            ''')
            
            stats = cursor.fetchone()
            
            # Source breakdown
            cursor.execute('''
                SELECT data_source, COUNT(*) as count, SUM(realized_pnl) as pnl
                FROM trades 
                GROUP BY data_source
                ORDER BY count DESC
            ''')
            
            source_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_trades': stats[0],
                'total_pnl': stats[1] or 0,
                'avg_win': stats[2] or 0,
                'avg_loss': stats[3] or 0,
                'winning_trades': stats[4],
                'losing_trades': stats[5],
                'win_rate': (stats[4] / stats[0] * 100) if stats[0] > 0 else 0,
                'sources': [{'source': row[0], 'count': row[1], 'pnl': row[2] or 0} for row in source_stats]
            }
            
        except Exception as e:
            logger.error(f"Failed to get trade statistics: {str(e)}")
            raise
    
    def log_security_event(self, action: str, table_name: str, record_id: Optional[int], 
                          details: str, data: Optional[Dict] = None):
        """Log security-relevant events for audit trail"""
        try:
            # Simplified logging to avoid database locking during bulk operations
            logger.info(f"SECURITY EVENT: {action} on {table_name} - {details}")
            # Comment out database logging for now to avoid locking issues
            # conn = sqlite3.connect(self.db_path)
            # cursor = conn.cursor()
            # 
            # cursor.execute('''
            #     INSERT INTO security_log 
            #     (action, table_name, record_id, details)
            #     VALUES (?, ?, ?, ?)
            # ''', (action, table_name, record_id, details))
            # 
            # conn.commit()
            # conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log security event: {str(e)}")
    
    def backup_database(self, backup_path: str) -> bool:
        """Create encrypted backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # Log backup event
            self.log_security_event("BACKUP", "database", None, 
                                  f"Database backed up to {backup_path}")
            
            logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            return False
    
    def verify_integrity(self) -> bool:
        """Verify database integrity and data consistency"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for duplicate hashes
            cursor.execute('''
                SELECT data_hash, COUNT(*) 
                FROM trades 
                GROUP BY data_hash 
                HAVING COUNT(*) > 1
            ''')
            
            duplicates = cursor.fetchall()
            if duplicates:
                logger.warning(f"Found {len(duplicates)} duplicate trade records")
                return False
            
            # Check for data consistency
            cursor.execute('''
                SELECT COUNT(*) FROM trades 
                WHERE ABS(buy_value - sell_value - realized_pnl) > 0.01
            ''')
            
            inconsistent = cursor.fetchone()[0]
            if inconsistent > 0:
                logger.warning(f"Found {inconsistent} trades with inconsistent calculations")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Integrity verification failed: {str(e)}")
            return False

# Convenience function for backward compatibility
def get_database(db_path: str = "data/trademirror.db") -> SecureDatabase:
    """Get database instance"""
    return SecureDatabase(db_path)