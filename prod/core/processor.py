import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import logging
import hashlib
import os
from datetime import datetime
import warnings
from io import StringIO, BytesIO
from typing import BinaryIO, TextIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSecurityError(Exception):
    """Custom exception for data security violations"""
    pass

class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

class ZerodhaDataProcessor:
    """
    Robust processor for Zerodha P&L data with security and validation features.
    Handles various edge cases and data quality issues.
    """
    
    def __init__(self):
        self.supported_extensions = ['.csv', '.xlsx', '.xls']
        self.required_columns = ['Symbol', 'Quantity', 'Buy Value', 'Sell Value', 'Realized P&L']
        self.sensitive_patterns = [
            r'\b\d{10}\b',  # Phone numbers
            r'[A-Z]{5}\d{4}[A-Z]',  # PAN numbers
            r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b'  # Credit card patterns
        ]
        
    def validate_file_security(self, file_source: Union[str, BinaryIO, TextIO]) -> bool:
        """
        Validate file security and check for potential threats.
        Supports both file paths and file-like objects.
        """
        try:
            file_name = ""
            file_size = 0
            file_ext = ""
            
            # Handle different types of file sources
            if isinstance(file_source, str):
                # File path
                file_name = os.path.basename(file_source)
                if not os.path.exists(file_source):
                    raise DataSecurityError(f"File not found: {file_source}")
                file_size = os.path.getsize(file_source)
                _, file_ext = os.path.splitext(file_source)
            elif hasattr(file_source, 'name'):
                # File-like object with name attribute
                file_name = os.path.basename(file_source.name)
                # Try to get file size
                if hasattr(file_source, 'size'):
                    file_size = file_source.size
                elif hasattr(file_source, 'seek') and hasattr(file_source, 'tell'):
                    # For file-like objects, determine size by seeking
                    current_pos = file_source.tell()
                    file_source.seek(0, 2)  # Seek to end
                    file_size = file_source.tell()
                    file_source.seek(current_pos)  # Restore position
                else:
                    # Default size if we can't determine
                    file_size = 0
                    
                _, file_ext = os.path.splitext(file_name)
            else:
                # Generic file-like object without name
                file_name = "uploaded_file"
                # Try to determine size
                if hasattr(file_source, 'seek') and hasattr(file_source, 'tell'):
                    current_pos = file_source.tell()
                    file_source.seek(0, 2)  # Seek to end
                    file_size = file_source.tell()
                    file_source.seek(current_pos)  # Restore position
                file_ext = ".bin"  # Default extension
                
            # Security checks
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                raise DataSecurityError(f"File too large: {file_size} bytes")
                
            if file_ext.lower() not in self.supported_extensions:
                raise DataSecurityError(f"Unsupported file type: {file_ext}")
                
            # Generate file hash for integrity checking
            if isinstance(file_source, str):
                with open(file_source, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
            else:
                # For file-like objects, read from current position
                current_pos = file_source.tell() if hasattr(file_source, 'tell') else 0
                file_source.seek(0)  # Go to beginning
                content = file_source.read()
                if isinstance(content, str):
                    content = content.encode('utf-8')
                file_hash = hashlib.sha256(content).hexdigest()
                # Restore file pointer
                if hasattr(file_source, 'seek'):
                    file_source.seek(current_pos)
                    
            logger.info(f"File security check passed for {file_name}. Hash: {file_hash[:16]}...")
            return True
            
        except DataSecurityError:
            raise
        except Exception as e:
            logger.error(f"Security validation failed: {str(e)}")
            raise DataSecurityError(f"Security validation failed: {str(e)}")
    
    def detect_header_row(self, df: pd.DataFrame) -> int:
        """
        Intelligently detect the header row in Zerodha data.
        """
        # First check if the first row already contains header-like values
        first_row = df.iloc[0]
        first_row_values = [str(val).strip() for val in first_row.values if pd.notna(val)]
        header_indicators = ['Symbol', 'Instrument', 'Tradingsymbol', 'Quantity', 'Buy Value', 'Realized P&L']
        
        # If first row contains header indicators, it's likely already the header
        if any(indicator in first_row_values for indicator in header_indicators):
            logger.info("Header detected in first row")
            return 0
        
        # Otherwise, look for header row in subsequent rows
        for idx, row in df.iterrows():
            # Skip first row since we already checked it
            if idx == 0:
                continue
            # Check if any header indicator is in this row
            row_values = [str(val).strip() for val in row.values if pd.notna(val)]
            if any(indicator in row_values for indicator in header_indicators):
                logger.info(f"Header detected at row index: {idx}")
                return idx
        
        # Fallback: look for the first row with mostly non-null values
        numeric_threshold = 0.7
        for idx, row in df.iterrows():
            if idx == 0:  # Skip first row for fallback check
                continue
            numeric_count = sum(pd.to_numeric(row, errors='coerce').notna())
            if numeric_count / len(row) >= numeric_threshold:
                logger.warning(f"Fallback header detection at row: {idx}")
                return idx
                
        # If no header found, assume first row is header (common case)
        logger.warning("No clear header found, assuming first row is header")
        return 0
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize column names.
        """
        # Strip whitespace and convert to title case
        df.columns = [str(col).strip().title() for col in df.columns]
        
        # Handle common column name variations
        column_mapping = {
            'Tradingsymbol': 'Symbol',
            'Instrument': 'Symbol',
            'Qty': 'Quantity',
            'Buy Amount': 'Buy Value',
            'Sell Amount': 'Sell Value',
            'P&L': 'Realized P&L',
            'Profit And Loss': 'Realized P&L'
        }
        
        df.rename(columns=column_mapping, inplace=True)
        return df
    
    def sanitize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove sensitive information and clean data.
        """
        # Remove columns that might contain sensitive data
        sensitive_columns = ['Client Id', 'Order Id', 'Trade Id']
        columns_to_drop = [col for col in sensitive_columns if col in df.columns]
        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
            logger.info(f"Dropped sensitive columns: {columns_to_drop}")
        
        # Clean text data
        text_columns = df.select_dtypes(include=[object]).columns
        for col in text_columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace common null representations
            df[col] = df[col].replace(['nan', 'None', 'null', ''], np.nan)
        
        return df
    
    def convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Safely convert string numbers to numeric values.
        """
        numeric_columns = ['Quantity', 'Buy Value', 'Sell Value', 'Realized P&L']
        
        for col in numeric_columns:
            if col in df.columns:
                try:
                    # Handle Indian number formatting (commas)
                    df[col] = df[col].astype(str).str.replace(',', '')
                    # Handle negative values in parentheses
                    df[col] = df[col].str.replace('(', '-').str.replace(')', '')
                    # Convert to numeric
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    logger.warning(f"Failed to convert column {col}: {str(e)}")
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def validate_data_integrity(self, df: pd.DataFrame) -> None:
        """
        Perform comprehensive data validation.
        """
        if df.empty:
            raise DataValidationError("DataFrame is empty")
        
        # Check for required columns
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise DataValidationError(f"Missing required columns: {missing_columns}")
        
        # Check for excessive null values
        null_percentages = df.isnull().sum() / len(df) * 100
        high_null_cols = null_percentages[null_percentages > 50]
        if not high_null_cols.empty:
            logger.warning(f"Columns with >50% null values: {high_null_cols.index.tolist()}")
        
        # Validate numeric ranges
        if 'Quantity' in df.columns:
            invalid_qty = df['Quantity'].lt(0).sum()
            if invalid_qty > 0:
                logger.warning(f"Found {invalid_qty} rows with negative quantities")
        
        logger.info("Data integrity validation passed")
    
    def calculate_derived_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate additional useful metrics.
        """
        # Basic win/loss calculation (only if Realized P&L exists)
        if 'Realized P&L' in df.columns:
            df['Win'] = df['Realized P&L'] > 0
            df['Loss'] = df['Realized P&L'] < 0
            df['Break_Even'] = df['Realized P&L'] == 0
        
        # Percentage returns (only if Buy Value exists)
        if 'Buy Value' in df.columns and 'Realized P&L' in df.columns:
            df['Return_Percentage'] = np.where(
                df['Buy Value'] != 0,
                (df['Realized P&L'] / df['Buy Value']) * 100,
                0
            )
        
        # Risk metrics (only if Quantity exists)
        if 'Quantity' in df.columns:
            df['Position_Size'] = abs(df['Quantity'])
            if 'Buy Value' in df.columns:
                df['Avg_Entry_Price'] = np.where(
                    df['Quantity'] != 0,
                    df['Buy Value'] / df['Quantity'],
                    0
                )
        
        # Time-based analysis (if date column exists)
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if date_columns:
            date_col = date_columns[0]
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                df['Day_of_Week'] = df[date_col].dt.day_name()
                df['Month'] = df[date_col].dt.month_name()
                df['Hour'] = df[date_col].dt.hour
            except Exception as e:
                logger.warning(f"Could not parse date/time column: {str(e)}")
        
        return df
    
    def load_zerodha_pnl(self, file_source: Union[str, BinaryIO, TextIO]) -> pd.DataFrame:
        """
        Main method to load and process Zerodha P&L data.
        Supports both file paths and file-like objects.
        """
        try:
            # Security validation
            self.validate_file_security(file_source)
            
            # Determine file type and load data
            if isinstance(file_source, str):
                # File path
                is_excel = file_source.endswith(('.xlsx', '.xls'))
            elif hasattr(file_source, 'name'):
                # File-like object with name
                is_excel = file_source.name.endswith(('.xlsx', '.xls'))
            else:
                # For other file-like objects, we need to determine type differently
                # This is a limitation - ideally the caller should specify
                is_excel = False  # Default to CSV
            
            # Load data based on type
            if is_excel:
                if isinstance(file_source, (str, BinaryIO)):
                    df = pd.read_excel(file_source)
                else:
                    # For text file objects, we need to handle differently
                    content = file_source.read()
                    if isinstance(content, str):
                        # Create a string IO object
                        bio = BytesIO(content.encode('utf-8'))
                        df = pd.read_excel(bio)
                    else:
                        df = pd.read_excel(BytesIO(content))
            else:
                if isinstance(file_source, (str, TextIO, BinaryIO)):
                    df = pd.read_csv(file_source)
                else:
                    content = file_source.read()
                    if isinstance(content, str):
                        df = pd.read_csv(StringIO(content))
                    else:
                        df = pd.read_csv(BytesIO(content))
            
            logger.info(f"Loaded data with shape: {df.shape}")
            
            # Detect and set header
            header_idx = self.detect_header_row(df)
            if header_idx > 0:
                df.columns = df.iloc[header_idx]
                df = df[header_idx + 1:].reset_index(drop=True)
            else:
                # Header is already in first row, just clean column names
                df = self.clean_column_names(df)
            
            # Clean and process data
            df = self.sanitize_data(df)
            df = self.convert_numeric_columns(df)
            
            # Validate processed data
            self.validate_data_integrity(df)
            
            # Calculate derived metrics
            df = self.calculate_derived_metrics(df)
            
            logger.info(f"Successfully processed data with {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to process Zerodha data: {str(e)}")
            raise
    
    def calculate_comprehensive_metrics(self, df: pd.DataFrame) -> Dict[str, Union[float, int, str]]:
        """
        Calculate comprehensive trading metrics.
        """
        try:
            # Ensure required columns exist
            required_for_metrics = ['Realized P&L']
            missing_cols = [col for col in required_for_metrics if col not in df.columns]
            if missing_cols:
                raise DataValidationError(f"Missing columns for metrics calculation: {missing_cols}")
            
            total_trades = len(df)
            winning_trades = df['Win'].sum() if 'Win' in df.columns else 0
            losing_trades = df['Loss'].sum() if 'Loss' in df.columns else 0
            break_even_trades = df['Break_Even'].sum() if 'Break_Even' in df.columns else 0
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            loss_rate = (losing_trades / total_trades) * 100 if total_trades > 0 else 0
            
            total_pnl = df['Realized P&L'].sum()
            avg_win = df[df['Realized P&L'] > 0]['Realized P&L'].mean() if winning_trades > 0 else 0
            avg_loss = df[df['Realized P&L'] < 0]['Realized P&L'].mean() if losing_trades > 0 else 0
            
            # Risk-reward ratio
            risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            # Profit factor
            gross_profit = df[df['Realized P&L'] > 0]['Realized P&L'].sum()
            gross_loss = abs(df[df['Realized P&L'] < 0]['Realized P&L'].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Maximum drawdown (approximate)
            cumulative_pnl = df['Realized P&L'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
            
            # Sharpe-like ratio (assuming risk-free rate = 0)
            if 'Return_Percentage' in df.columns:
                returns_std = df['Return_Percentage'].std()
                sharpe_ratio = df['Return_Percentage'].mean() / returns_std if returns_std != 0 else 0
            else:
                sharpe_ratio = 0
            
            # Consecutive wins/losses
            consecutive_wins = self._calculate_consecutive_trades(df, 'Win') if 'Win' in df.columns else 0
            consecutive_losses = self._calculate_consecutive_trades(df, 'Loss') if 'Loss' in df.columns else 0
            
            metrics = {
                "Total_P&L": round(total_pnl, 2),
                "Total_Trades": total_trades,
                "Winning_Trades": int(winning_trades),
                "Losing_Trades": int(losing_trades),
                "Break_Even_Trades": int(break_even_trades),
                "Win_Rate": round(win_rate, 2),
                "Loss_Rate": round(loss_rate, 2),
                "Average_Win": round(avg_win, 2),
                "Average_Loss": round(avg_loss, 2),
                "Risk_Reward_Ratio": round(risk_reward, 2) if risk_reward != float('inf') else "Infinite",
                "Profit_Factor": round(profit_factor, 2) if profit_factor != float('inf') else "Infinite",
                "Max_Drawdown": round(max_drawdown, 2),
                "Sharpe_Ratio": round(sharpe_ratio, 2),
                "Max_Consecutive_Wins": consecutive_wins,
                "Max_Consecutive_Losses": consecutive_losses,
                "Best_Single_Trade": round(df['Realized P&L'].max(), 2),
                "Worst_Single_Trade": round(df['Realized P&L'].min(), 2)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {str(e)}")
            raise
    
    def _calculate_consecutive_trades(self, df: pd.DataFrame, condition_col: str) -> int:
        """
        Calculate maximum consecutive wins or losses.
        """
        if condition_col not in df.columns:
            return 0
            
        consecutive_count = 0
        max_consecutive = 0
        
        for value in df[condition_col]:
            if value:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
                
        return max_consecutive

# Convenience functions for backward compatibility
def load_zerodha_pnl(file_source: Union[str, BinaryIO, TextIO]) -> pd.DataFrame:
    """Backward compatible function that supports file paths and file-like objects"""
    processor = ZerodhaDataProcessor()
    return processor.load_zerodha_pnl(file_source)

def calculate_metrics(df: pd.DataFrame) -> Dict[str, Union[float, int, str]]:
    """Backward compatible function"""
    processor = ZerodhaDataProcessor()
    return processor.calculate_comprehensive_metrics(df)