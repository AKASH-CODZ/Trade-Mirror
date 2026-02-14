#!/usr/bin/env python3
"""
Simple example showing how to use the TradeMirror processor.
"""

from processor import ZerodhaDataProcessor
import pandas as pd

def main():
    print("🎯 TradeMirror Usage Example")
    print("=" * 40)
    
    # Initialize the processor
    processor = ZerodhaDataProcessor()
    
    try:
        # Load sample data
        print("1. Loading sample trading data...")
        df = processor.load_zerodha_pnl('data/sample_zerodha_data.csv')
        print(f"   ✅ Loaded {len(df)} trading records")
        
        # Display basic information
        print("\n2. Data Overview:")
        print(f"   - Columns: {len(df.columns)}")
        print(f"   - Date Range: {df['Time'].min()} to {df['Time'].max()}")
        print(f"   - Symbols Traded: {df['Symbol'].nunique()}")
        
        # Calculate metrics
        print("\n3. Performance Metrics:")
        metrics = processor.calculate_comprehensive_metrics(df)
        
        # Display key metrics
        print(f"   📊 Total P&L: ₹{metrics['Total_P&L']:,.2f}")
        print(f"   🎯 Win Rate: {metrics['Win_Rate']:.1f}% ({metrics['Winning_Trades']}/{metrics['Total_Trades']} trades)")
        print(f"   ⚖️  Risk-Reward Ratio: 1:{metrics['Risk_Reward_Ratio']}")
        print(f"   💰 Profit Factor: {metrics['Profit_Factor']}")
        print(f"   📉 Max Drawdown: ₹{metrics['Max_Drawdown']:,.2f}")
        
        # Performance insights
        print("\n4. Performance Insights:")
        if metrics['Win_Rate'] > 60:
            print("   ✅ Good win rate - you're beating the market!")
        elif metrics['Win_Rate'] > 50:
            print("   ⚠️  Decent win rate - room for improvement")
        else:
            print("   ❌ Low win rate - consider strategy review")
            
        if metrics['Risk_Reward_Ratio'] > 2:
            print("   ✅ Excellent risk-reward profile")
        elif metrics['Risk_Reward_Ratio'] > 1:
            print("   ⚠️  Acceptable risk-reward ratio")
        else:
            print("   ❌ Poor risk-reward - too much risk for reward")
            
        # Best and worst performers
        print("\n5. Top Performers:")
        best_trades = df.nlargest(3, 'Realized P&L')[['Symbol', 'Realized P&L', 'Time']]
        for _, trade in best_trades.iterrows():
            print(f"   📈 {trade['Symbol']}: ₹{trade['Realized P&L']:,.2f} ({trade['Time']})")
            
        print("\n6. Areas to Improve:")
        worst_trades = df.nsmallest(3, 'Realized P&L')[['Symbol', 'Realized P&L', 'Time']]
        for _, trade in worst_trades.iterrows():
            print(f"   📉 {trade['Symbol']}: ₹{trade['Realized P&L']:,.2f} ({trade['Time']})")
            
        # Time-based analysis
        if 'Day_of_Week' in df.columns:
            print("\n7. Day-wise Performance:")
            daily_perf = df.groupby('Day_of_Week')['Realized P&L'].agg(['sum', 'count', 'mean'])
            best_day = daily_perf['sum'].idxmax()
            worst_day = daily_perf['sum'].idxmin()
            print(f"   🏆 Best Day: {best_day} (₹{daily_perf.loc[best_day, 'sum']:,.2f})")
            print(f"   😞 Worst Day: {worst_day} (₹{daily_perf.loc[worst_day, 'sum']:,.2f})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("✨ Analysis Complete!")
    print("Ready for Day 2: Building the Streamlit dashboard and AI integration")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)