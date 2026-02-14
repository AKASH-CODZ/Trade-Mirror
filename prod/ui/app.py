import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import logging
from typing import Optional
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports from organized structure
from prod.core.processor import ZerodhaDataProcessor
from prod.core.database import SecureDatabase
from prod.core.ai_coach import SecureAICoach, CoachingRequest
from prod.core.visuals import create_professional_dashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="TradeMirror Pro - Executive Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00ff00;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #262730;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .insight-box {
        border-left: 4px solid #00ff00;
        padding: 1rem;
        margin: 1rem 0;
        background-color: rgba(0, 255, 0, 0.1);
    }
    .warning-box {
        border-left: 4px solid #ff4b4b;
        padding: 1rem;
        margin: 1rem 0;
        background-color: rgba(255, 75, 75, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def get_components():
    """Initialize all components with caching"""
    processor = ZerodhaDataProcessor()
    database = SecureDatabase()
    ai_coach = SecureAICoach()
    return processor, database, ai_coach

def main():
    """Main application entry point"""
    
    # Professional header
    st.markdown('<div class="main-header">📊 TradeMirror Pro</div>', unsafe_allow_html=True)
    st.markdown("*Professional Trading Analytics & AI Coaching Platform*")
    
    # Initialize components
    try:
        processor, database, ai_coach = get_components()
    except Exception as e:
        st.error(f"Failed to initialize components: {str(e)}")
        return
    
    # Sidebar with professional controls
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Date range filter
        st.subheader("📅 Time Period")
        date_options = {
            "Last 30 Days": 30,
            "Last 90 Days": 90,
            "Year to Date": "YTD",
            "All Time": "ALL"
        }
        
        selected_period = st.selectbox("Select Time Range:", list(date_options.keys()))
        
        # AI Persona Selection
        st.subheader("🤖 AI Coach Persona")
        personas = {
            "Professional": "professional",
            "Ruthless Manager": "ruthless",
            "Supportive Coach": "supportive",
            "Data Scientist": "data_scientist",
            "Veteran Mentor": "mentor"
        }
        
        selected_persona = st.selectbox(
            "Choose Coaching Style:",
            list(personas.keys()),
            index=0
        )
        
        # System Status
        st.subheader("⚙️ System Status")
        
        # Database status
        try:
            stats = database.get_trade_statistics()
            st.metric("Total Trades", f"{stats['total_trades']:,}")
            st.metric("Total P&L", f"₹{stats['total_pnl']:,.2f}")
            st.progress(stats['win_rate'] / 100)
            st.caption(f"Win Rate: {stats['win_rate']:.1f}%")
        except Exception as e:
            st.warning("Database initializing...")
        
        # AI Coach status
        if ai_coach.health_check():
            st.success("🧠 AI Coach Online")
            models = ai_coach.get_available_models()
            if models:
                st.caption(f"Models: {', '.join(models[:2])}")
        else:
            st.error("🧠 AI Coach Offline")
            st.caption("Start Ollama: `ollama serve`")
        
        st.divider()
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Executive Dashboard", 
        "📂 Data Management", 
        "🤖 AI Performance Coach", 
        "📊 Detailed Analytics"
    ])
    
    # Tab 1: Executive Dashboard
    with tab1:
        st.header("📈 Executive Performance Dashboard")
        
        # Load and filter data based on selected period
        try:
            all_trades = database.get_trades()
            
            if not all_trades.empty and 'Date' in all_trades.columns:
                # Apply date filtering
                if selected_period == "YTD":
                    start_date = datetime(datetime.now().year, 1, 1)
                    filtered_df = all_trades[all_trades['Date'] >= start_date]
                elif selected_period == "ALL":
                    filtered_df = all_trades
                else:
                    days_back = date_options[selected_period]
                    start_date = datetime.now() - timedelta(days=days_back)
                    filtered_df = all_trades[all_trades['Date'] >= start_date]
                
                if not filtered_df.empty:
                    # Create professional dashboard
                    with st.spinner("Generating professional dashboard..."):
                        dashboard = create_professional_dashboard(filtered_df)
                        summary_stats = dashboard['summary_stats']
                    
                    # Key Performance Indicators
                    st.subheader("🔑 Key Performance Indicators")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total P&L", f"₹{summary_stats['total_pnl']:,.2f}", 
                                delta=f"{summary_stats['win_rate']:.1f}% Win Rate")
                    with col2:
                        st.metric("Total Trades", summary_stats['total_trades'],
                                delta=f"{summary_stats['winning_trades']} Winners")
                    with col3:
                        st.metric("Avg Win/Loss", f"₹{summary_stats['avg_win']:,.2f}",
                                delta=f"₹{summary_stats['avg_loss']:,.2f}")
                    with col4:
                        st.metric("Profit Factor", f"{summary_stats['profit_factor']:.2f}",
                                delta=f"Max Drawdown: ₹{summary_stats.get('worst_day_pnl', 0):,.2f}")
                    
                    # Professional Charts
                    st.subheader("📊 Performance Visualizations")
                    
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        st.plotly_chart(dashboard['equity_curve'], use_container_width=True)
                    
                    with chart_col2:
                        st.plotly_chart(dashboard['weekday_heatmap'], use_container_width=True)
                    
                    # Monthly Performance
                    st.plotly_chart(dashboard['monthly_performance'], use_container_width=True)
                    
                    # AI-Generated Insights
                    st.subheader("🤖 AI-Powered Insights")
                    
                    if ai_coach.health_check():
                        with st.spinner("Getting professional analysis..."):
                            ai_request = CoachingRequest(
                                metrics=summary_stats,
                                recent_trades=filtered_df.tail(10),
                                persona=personas[selected_persona]
                            )
                            
                            ai_insight = ai_coach.get_coaching_advice(ai_request)
                            
                            if ai_insight['status'] == 'success':
                                st.markdown(f"""
                                <div class="insight-box">
                                <h4>{ai_insight['persona_name']} Analysis</h4>
                                <p>{ai_insight['advice']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.warning("AI analysis temporarily unavailable")
                    else:
                        st.info("Start Ollama service for AI-powered insights")
                
                else:
                    st.info("No trading data available for the selected time period")
            else:
                st.warning("No trading data found in database")
                
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")
            logger.error(f"Dashboard error: {str(e)}")
    
    # Tab 2: Data Management
    with tab2:
        st.header("📂 Trading Data Management")
        
        # File Upload Section
        st.subheader("📤 Upload Trading Data")
        uploaded_file = st.file_uploader(
            "Upload your trading data (CSV/XLSX)", 
            type=['csv', 'xlsx', 'xls'],
            help="Supported formats: Zerodha, Upstox, Groww, and generic trading data"
        )
        
        if uploaded_file:
            try:
                with st.spinner("Processing your data..."):
                    # Process file
                    df = processor.load_zerodha_pnl(uploaded_file)
                    
                    if not df.empty:
                        st.success(f"✅ Successfully processed {len(df)} trades!")
                        
                        # Store in database
                        source_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        stored_count = database.store_trades(df, source_name)
                        st.info(f"💾 Stored {stored_count} new unique trades in local database")
                        
                        # Display data preview
                        st.subheader("Data Preview")
                        st.dataframe(df.head(10), use_container_width=True)
                        
                        # Calculate and display metrics
                        st.subheader("Performance Metrics")
                        metrics = processor.calculate_comprehensive_metrics(df)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total P&L", f"₹{metrics['Total_P&L']:,.2f}")
                        col2.metric("Win Rate", f"{metrics['Win_Rate']:.1f}%")
                        col3.metric("Risk:Reward", f"1:{metrics['Risk_Reward_Ratio']:.2f}")
                        col4.metric("Profit Factor", f"{metrics['Profit_Factor']:.2f}")
                        
                        # Store processed data in session for AI coaching
                        st.session_state.processed_data = {
                            'df': df,
                            'metrics': metrics,
                            'source': 'file_upload'
                        }
                        
                    else:
                        st.error("No valid trading data found in the file")
                        
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                logger.error(f"File processing error: {str(e)}")
        
        # Database Statistics
        st.subheader("🗄️ Database Statistics")
        try:
            db_stats = database.get_trade_statistics()
            
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.metric("Total Records", f"{db_stats['total_trades']:,}")
                st.metric("Cumulative P&L", f"₹{db_stats['total_pnl']:,.2f}")
            
            with stat_col2:
                st.metric("Overall Win Rate", f"{db_stats['win_rate']:.1f}%")
                st.metric("Data Sources", len(db_stats['sources']))
            
            if db_stats['sources']:
                st.subheader("Data Sources Breakdown")
                for source in db_stats['sources']:
                    st.write(f"• **{source['source']}**: {source['count']} trades (₹{source['pnl']:,.2f})")
                    
        except Exception as e:
            st.warning("Database statistics unavailable")
    
    # Tab 3: AI Performance Coach
    with tab3:
        st.header("🤖 AI Performance Coach")
        
        # Check if we have data to analyze
        if 'processed_data' not in st.session_state:
            st.info("📤 Process some trading data first (use Data Management tab)")
            return
        
        data = st.session_state.processed_data
        df = data['df']
        metrics = data['metrics']
        
        st.subheader("Analysis Ready")
        st.write(f"**Data Source:** {data['source']}")
        st.write(f"**Trades Analyzed:** {len(df)}")
        
        # Persona-based coaching
        st.subheader(f"🎤 {selected_persona} Coaching Session")
        
        if st.button("🧠 Get AI Coaching Advice", type="primary"):
            try:
                with st.spinner(f"Getting {selected_persona} analysis..."):
                    # Prepare coaching request
                    request = CoachingRequest(
                        metrics=metrics,
                        recent_trades=df.tail(10),
                        trading_style="mixed",
                        risk_tolerance="moderate",
                        persona=personas[selected_persona]
                    )
                    
                    # Get advice
                    advice_data = ai_coach.get_coaching_advice(request)
                    
                    if advice_data['status'] == 'success':
                        st.success("✅ Coaching advice received!")
                        
                        # Display advice with proper formatting
                        st.markdown(f"""
                        <div class="insight-box">
                        <h4>{advice_data['persona_name']}</h4>
                        <p>{advice_data['advice']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Store coaching session
                        st.session_state.coaching_sessions = st.session_state.get('coaching_sessions', [])
                        st.session_state.coaching_sessions.append({
                            'timestamp': datetime.now(),
                            'persona': advice_data['persona_name'],
                            'advice': advice_data['advice'],
                            'metrics': metrics
                        })
                        
                    else:
                        st.error(f"Coaching failed: {advice_data.get('message', 'Unknown error')}")
                        
            except Exception as e:
                st.error(f"Coaching error: {str(e)}")
                logger.error(f"AI coaching error: {str(e)}")
        
        # Quick assessment
        st.subheader("⚡ Quick Performance Snapshot")
        
        if st.button("Get Instant Assessment"):
            try:
                quick_assessment = ai_coach.get_quick_assessment(
                    metrics.get('Total_P&L', 0),
                    metrics.get('Win_Rate', 0),
                    metrics.get('Risk_Reward_Ratio', 1),
                    personas[selected_persona]
                )
                st.info(f"**{selected_persona} Assessment:** {quick_assessment}")
            except Exception as e:
                st.error(f"Quick assessment failed: {str(e)}")
    
    # Tab 4: Detailed Analytics
    with tab4:
        st.header("📊 Detailed Trading Analytics")
        
        try:
            all_trades = database.get_trades()
            
            if not all_trades.empty:
                # Time-based analysis
                st.subheader("📅 Time-Based Performance")
                
                # Daily performance
                daily_perf = all_trades.groupby(all_trades['Date'].dt.date)['Realized P&L'].sum()
                st.line_chart(daily_perf)
                
                # Symbol performance
                st.subheader("💹 Symbol Performance")
                symbol_perf = all_trades.groupby('Symbol')['Realized P&L'].agg(['sum', 'count', 'mean']).round(2)
                symbol_perf.columns = ['Total_P&L', 'Trade_Count', 'Avg_P&L']
                symbol_perf = symbol_perf.sort_values('Total_P&L', ascending=False)
                st.dataframe(symbol_perf, use_container_width=True)
                
                # Trade distribution
                st.subheader("📊 Trade Distribution Analysis")
                
                dist_col1, dist_col2 = st.columns(2)
                with dist_col1:
                    win_loss_counts = all_trades['Win'].value_counts()
                    st.bar_chart(win_loss_counts)
                
                with dist_col2:
                    # P&L distribution
                    st.scatter_chart(all_trades[['Date', 'Realized P&L']].set_index('Date'))
                    
            else:
                st.info("No detailed analytics available - upload trading data first")
                
        except Exception as e:
            st.error(f"Analytics error: {str(e)}")
    
    # Footer
    st.divider()
    st.caption("📊 TradeMirror Pro - Professional Trading Analytics Platform | 100% Local Processing | Zero External Data Transmission")

if __name__ == "__main__":
    main()