#!/usr/bin/env python3
"""
Demonstration script for TradeMirror processor.
Shows various features and capabilities with sample data.
"""

import pandas as pd
import sys
from pathlib import Path
from processor import ZerodhaDataProcessor, DataSecurityError, DataValidationError

def demonstrate_basic_processing():
    """Demonstrate basic data processing capabilities"""
    print("📊 BASIC DATA PROCESSING DEMONSTRATION")
    print("="*50)
    
    processor = ZerodhaDataProcessor()
    
    # Process sample data
    sample_file = "data/sample_zerodha_data.csv"
    try:
        print(f"Processing file: {sample_file}")
        df = processor.load_zerodha_pnl(sample_file)
        
        print(f"\n✅ Successfully loaded {len(df)} records")
        print(f"Columns: {list(df.columns)}")
        
        # Show first few records
        print("\n📋 First 5 records:")
        print(df.head().to_string(index=False))
        
        # Calculate metrics
        metrics = processor.calculate_comprehensive_metrics(df)
        print("\n📈 Key Metrics:")
        print(f"Total P&L: ₹{metrics['Total_P&L']:,.2f}")
        print(f"Win Rate: {metrics['Win_Rate']:.1f}%")
        print(f"Risk-Reward Ratio: 1:{metrics['Risk_Reward_Ratio']}")
        print(f"Profit Factor: {metrics['Profit_Factor']}")
        print(f"Max Drawdown: ₹{metrics['Max_Drawdown']:,.2f}")
        
    except Exception as e:
        print(f"❌ Error processing sample data: {str(e)}")

def demonstrate_edge_case_handling():
    """Demonstrate handling of problematic data"""
    print("\n\n🔍 EDGE CASE HANDLING DEMONSTRATION")
    print("="*50)
    
    processor = ZerodhaDataProcessor()
    
    # Process problematic data
    problem_file = "data/problematic_data.csv"
    try:
        print(f"Processing problematic file: {problem_file}")
        df = processor.load_zerodha_pnl(problem_file)
        
        print(f"\n✅ Successfully handled problematic data with {len(df)} records")
        
        # Show data quality insights
        print(f"\n📋 Data Quality Report:")
        print(f"- Records with missing symbols: {(df['Symbol'].isna()).sum()}")
        print(f"- Records with invalid quantities: {(pd.to_numeric(df['Quantity'], errors='coerce').isna()).sum()}")
        print(f"- Winning trades: {df['Win'].sum()}")
        print(f"- Losing trades: {df['Loss'].sum()}")
        
        metrics = processor.calculate_comprehensive_metrics(df)
        print(f"\n📈 Processed Metrics:")
        print(f"Total P&L: ₹{metrics['Total_P&L']:,.2f}")
        print(f"Win Rate: {metrics['Win_Rate']:.1f}%")
        
    except Exception as e:
        print(f"❌ Error processing problematic data: {str(e)}")

def demonstrate_security_features():
    """Demonstrate security validation features"""
    print("\n\n🛡️ SECURITY FEATURES DEMONSTRATION")
    print("="*50)
    
    processor = ZerodhaDataProcessor()
    
    # Test security validation
    print("Testing file security validation...")
    
    # Test unsupported file type
    try:
        processor.validate_file_security("malicious.exe")
        print("❌ Security check failed - should have rejected .exe file")
    except DataSecurityError as e:
        print(f"✅ Security check passed - correctly rejected: {str(e)}")
    
    # Test normal file (this should work)
    try:
        processor.validate_file_security("data/sample_zerodha_data.csv")
        print("✅ Security check passed - accepted valid CSV file")
    except DataSecurityError as e:
        print(f"❌ Unexpected security error: {str(e)}")

def demonstrate_performance_analysis():
    """Demonstrate advanced performance metrics"""
    print("\n\n📈 ADVANCED PERFORMANCE ANALYSIS")
    print("="*50)
    
    processor = ZerodhaDataProcessor()
    
    try:
        df = processor.load_zerodha_pnl("data/sample_zerodha_data.csv")
        metrics = processor.calculate_comprehensive_metrics(df)
        
        print("Advanced Trading Metrics:")
        print("-" * 30)
        
        # Performance ratios
        print(f"Sharpe Ratio: {metrics['Sharpe_Ratio']:.2f}")
        print(f"Profit Factor: {metrics['Profit_Factor']}")
        print(f"Risk-Reward Ratio: 1:{metrics['Risk_Reward_Ratio']}")
        
        # Trade statistics
        print(f"\nTrade Statistics:")
        print(f"Total Trades: {metrics['Total_Trades']}")
        print(f"Winning Trades: {metrics['Winning_Trades']}")
        print(f"Losing Trades: {metrics['Losing_Trades']}")
        print(f"Break-even Trades: {metrics['Break_Even_Trades']}")
        
        # Consecutive performance
        print(f"\nConsecutive Performance:")
        print(f"Max Consecutive Wins: {metrics['Max_Consecutive_Wins']}")
        print(f"Max Consecutive Losses: {metrics['Max_Consecutive_Losses']}")
        
        # Best/worst trades
        print(f"\nExtreme Values:")
        print(f"Best Single Trade: ₹{metrics['Best_Single_Trade']:,.2f}")
        print(f"Worst Single Trade: ₹{metrics['Worst_Single_Trade']:,.2f}")
        print(f"Average Win: ₹{metrics['Average_Win']:,.2f}")
        print(f"Average Loss: ₹{metrics['Average_Loss']:,.2f}")
        
    except Exception as e:
        print(f"❌ Error in performance analysis: {str(e)}")

def main():
    """Main demonstration function"""
    print("🪞 Trade-Mirror Processor Demonstration")
    print("========================================")
    
    # Run all demonstrations
    demonstrate_basic_processing()
    demonstrate_edge_case_handling()
    demonstrate_security_features()
    demonstrate_performance_analysis()
    
    print("\n" + "="*60)
    print("🎉 Demonstration Complete!")
    print("The processor successfully handles:")
    print("• Standard Zerodha data formats")
    print("• Problematic data with missing/invalid values")
    print("• Security validation and threat prevention")
    print("• Comprehensive performance metrics")
    print("• Edge case handling and data cleaning")
    print("="*60)

if __name__ == '__main__':
    main()