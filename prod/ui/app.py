"""
TradeMirror Pro - Executive Trading Dashboard
Day 5: Decentralized AI Architecture with Connection Manager
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import base64
import requests
from datetime import datetime
import logging
from typing import Optional
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Local imports
from prod.core.processor import ZerodhaDataProcessor
from prod.core.database import SecureDatabase
from prod.core.visuals import create_professional_dashboard
from prod.core.ai_coach import get_analysis  # Updated AI router
from prod.core.secrets_manager import secrets_manager, save_api_key, get_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="TradeMirror Pro - Executive Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (The "Production" Look) ---
st.markdown("""
<style>
/* Hero Upload Box */
.upload-box {
    border: 3px dashed #00ff00;
    padding: 60px;
    border-radius: 20px;
    text-align: center;
    background: linear-gradient(145deg, #0e1117, #1a1c23);
    margin: 30px 0;
    transition: all 0.3s ease;
    box-shadow: 0 10px 30px rgba(0, 255, 0, 0.1);
}

.upload-box:hover {
    border-color: #00cc00;
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0, 255, 0, 0.2);
}

.upload-box h3 {
    color: #00ff00;
    font-size: 2rem;
    margin-bottom: 15px;
}

.upload-box p {
    color: #aaa;
    font-size: 1.1rem;
}

/* Metric Cards */
.metric-card {
    background: linear-gradient(145deg, #262730, #1e1e1e);
    padding: 25px;
    border-radius: 15px;
    border-left: 5px solid #00ff00;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
    margin-bottom: 20px;
}

/* Header Styling */
.main-header {
    font-size: 3rem;
    font-weight: bold;
    color: #00ff00;
    text-align: center;
    margin: 2rem 0;
    text-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
}

.tagline {
    text-align: center;
    color: #aaa;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}

/* Connection Manager Styling */
.connection-manager {
    background: linear-gradient(145deg, #1a1c23, #262730);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #00ff00;
}

.compute-option {
    background-color: #262730;
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid #363740;
}

.compute-active {
    border-color: #00ff00;
    background: linear-gradient(145deg, #1a2c23, #1e3730);
}

/* Button Styles */
.stButton > button {
    background: linear-gradient(45deg, #00ff00, #00cc00);
    color: #000;
    border: none;
    border-radius: 10px;
    padding: 15px 30px;
    font-weight: bold;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 255, 0, 0.4);
}

/* File Uploader Styling */
.stFileUploader {
    padding-top: 20px;
}

.stFileUploader > div {
    background-color: transparent !important;
    border: none !important;
}

/* Dashboard Sections */
.dashboard-section {
    background-color: #1e1e1e;
    border-radius: 15px;
    padding: 25px;
    margin: 20px 0;
    border: 1px solid #363740;
}

.section-title {
    color: #00ff00;
    font-size: 1.8rem;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #00ff00;
}

/* AI Analysis Section */
.ai-analysis-box {
    background: linear-gradient(145deg, #1a1c23, #262730);
    border-radius: 15px;
    padding: 25px;
    margin-top: 30px;
    border: 1px solid #00ff00;
}

/* Toast Messages */
.stToast {
    background-color: #00ff00 !important;
    color: #000 !important;
}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'df' not in st.session_state:
    st.session_state.df = None

if 'ai_config' not in st.session_state:
    # Default to community cloud
    st.session_state.ai_config = {
        "type": "cloud_shared",
        "key": None,  # Will be loaded from secrets when needed
        "url": None
    }

# --- HEADER SECTION ---
st.markdown('<div class="main-header">🚀 TradeMirror Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Decentralized AI Trading Analytics</div>', unsafe_allow_html=True)

# --- ⚙️ SIDEBAR: RESTRICTED CONTROL CENTER ---
with st.sidebar:
    st.markdown('<div class="connection-manager">', unsafe_allow_html=True)
    st.header("⚡ Compute Settings")
    
    # SIMPLIFIED MODES: No more "Bring Your Own Key"
    compute_mode = st.radio(
        "Select Performance Tier:",
        ["☁️ Cloud (Community)", "🚀 Professional (Local/Admin)"],
        help="Community is free. Professional connects to dedicated GPU infrastructure."
    )

    # --- OPTION A: CLOUD (The Default for Clients) ---
    if compute_mode == "☁️ Cloud (Community)":
        st.success("🟢 Connected to TradeMirror Cloud")
        st.caption("Powered by Groq LPU™ Inference Engine")
        
        # Load the key securely from Secrets
        try:
            if "GROQ_API_KEY" in st.secrets:
                st.session_state['ai_config'] = {
                    "type": "cloud_shared", 
                    "key": st.secrets["GROQ_API_KEY"], 
                    "url": None
                }
            else:
                st.error("🚨 System Error: Cloud Key not found in Secrets.")
        except Exception as e:
            st.error(f"🚨 Configuration Error: {str(e)}")

    # --- OPTION B: LOCAL (Locked for You) ---
    elif compute_mode == "🚀 Professional (Local/Admin)":
        st.warning("🔒 Admin Access Required")
        
        # Simple Password Lock
        admin_pass = st.text_input("Enter Admin Password:", type="password")
        
        # Check against the password you set in Secrets
        try:
            correct_password = st.secrets.get("ADMIN_PASSWORD", "admin")
            if admin_pass == correct_password: 
                st.info("🔓 Access Granted: RTX 5070 Connection")
                local_url = st.text_input("Ngrok Tunnel URL:", placeholder="https://xyz.ngrok-free.app")
                
                if local_url:
                    st.session_state['ai_config'] = {
                        "type": "local_tunnel",
                        "key": None,
                        "url": f"{local_url.rstrip('/')}/api/generate"
                    }
                    if st.button("Test Local Connection 🔧"):
                        try:
                            test_url = f"{local_url.rstrip('/')}/api/tags"
                            response = requests.get(test_url, timeout=10)
                            if response.status_code == 200:
                                st.success("✅ GPU Connected!")
                            else:
                                st.error(f"❌ Server responded with status {response.status_code}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Connection failed: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Unexpected error: {str(e)}")
            else:
                st.caption("Restricted to Enterprise Clients only.")
        except Exception as e:
            st.error(f"🚨 Admin authentication error: {str(e)}")

    st.divider()
    
    # Display current connection status
    current_config = st.session_state.get('ai_config', {})
    st.subheader("📡 Current Setup")
    config_type = current_config.get('type', 'Not configured')
    type_labels = {
        'cloud_shared': 'Community Cloud',
        'local_tunnel': 'Local GPU Tunnel'
    }
    st.info(f"**Mode:** {type_labels.get(config_type, config_type)}")
    
    if current_config.get('url'):
        st.code(current_config['url'], language='url')
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 1. THE HERO UPLOAD SECTION ---
if st.session_state.df is None:
    st.markdown('''
    <div class="upload-box">
        <h3>📂 Drag & Drop Your Broker CSV Here</h3>
        <p>Supports Zerodha, Upstox, Groww, and other brokers</p>
        <p style="color: #00ff00; margin-top: 15px;">⚡ Auto-sorted timeline • Instant analysis • Secure processing</p>
    </div>
    ''', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "", 
        type=['csv', 'xlsx', 'xls'], 
        label_visibility="collapsed",
        key="hero_uploader"
    )
    
    if uploaded_file:
        with st.spinner("Processing your trading data..."):
            try:
                processor = ZerodhaDataProcessor()
                raw_df = processor.load_zerodha_pnl(uploaded_file)
                
                # --- 2. AUTO-SORTING LOGIC ---
                if 'Date' in raw_df.columns:
                    # Convert to datetime and sort OLD -> NEW
                    raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
                    raw_df = raw_df.dropna(subset=['Date'])  # Remove invalid dates
                    raw_df = raw_df.sort_values(by='Date', ascending=True).reset_index(drop=True)
                    
                    st.session_state.df = raw_df
                    
                    # Store in database
                    database = SecureDatabase()
                    source_name = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    stored_count = database.store_trades(raw_df, source_name)
                    
                    st.success(f"✅ Data Loaded & Timeline Sorted! ({len(raw_df)} trades processed, {stored_count} new records)")
                    st.balloons()
                    st.rerun()  # Refresh to show dashboard
                else:
                    st.error("⚠️ CSV missing 'Date' column. Cannot build timeline.")
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                logger.error(f"File processing error: {str(e)}")

# --- THE DASHBOARD (Only visible after upload) ---
if st.session_state.df is not None:
    df = st.session_state.df
    
    # --- 3. FEATURE EXTRACTION (Vital Signs) ---
    total_pnl = df['Realized P&L'].sum()
    win_trades = df[df['Realized P&L'] > 0]
    loss_trades = df[df['Realized P&L'] < 0]
    win_rate = (len(win_trades) / len(df)) * 100 if len(df) > 0 else 0
    
    # Extract "Best Day" and "Worst Day" for AI Context
    if len(df) > 0:
        best_day_row = df.loc[df['Realized P&L'].idxmax()]
        worst_day_row = df.loc[df['Realized P&L'].idxmin()]
        best_day = best_day_row['Date'].strftime('%Y-%m-%d')
        worst_day = worst_day_row['Date'].strftime('%Y-%m-%d')
        best_day_pnl = best_day_row['Realized P&L']
        worst_day_pnl = worst_day_row['Realized P&L']
    else:
        best_day = worst_day = "N/A"
        best_day_pnl = worst_day_pnl = 0

    # --- KEY METRICS ROW ---
    st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔑 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f'''
        <div class="metric-card">
            <h3>💰 Net P&L</h3>
            <h2 style="color: {"#00ff00" if total_pnl >= 0 else "#ff4b4b"}">₹{total_pnl:,.2f}</h2>
        </div>
        ''', unsafe_allow_html=True)
    
    with c2:
        st.markdown(f'''
        <div class="metric-card">
            <h3>🎯 Win Rate</h3>
            <h2 style="color: {"#00ff00" if win_rate >= 60 else "#ff9500"}">{win_rate:.1f}%</h2>
        </div>
        ''', unsafe_allow_html=True)
    
    with c3:
        st.markdown(f'''
        <div class="metric-card">
            <h3>📅 Best Day</h3>
            <h2 style="color: #00ff00">{best_day}</h2>
            <p style="color: #aaa; font-size: 0.9rem;">₹{best_day_pnl:,.2f}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with c4:
        st.markdown(f'''
        <div class="metric-card">
            <h3>📉 Worst Day</h3>
            <h2 style="color: #ff4b4b">{worst_day}</h2>
            <p style="color: #aaa; font-size: 0.9rem;">₹{worst_day_pnl:,.2f}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- PERFORMANCE TIMELINE CHART ---
    st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 Performance Timeline</div>', unsafe_allow_html=True)
    
    # Interactive Timeline Chart
    df['Cumulative P&L'] = df['Realized P&L'].cumsum()
    fig = px.area(
        df, 
        x='Date', 
        y='Cumulative P&L',
        title="Cumulative Profit & Loss Over Time",
        color_discrete_sequence=['#00ff00'],
        template='plotly_dark'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        title_font=dict(size=20, color='#00ff00')
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- MONTHLY PERFORMANCE HEATMAP ---
    st.markdown('<div class="dashboard-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Monthly Performance</div>', unsafe_allow_html=True)
    
    try:
        dashboard = create_professional_dashboard(df)
        st.plotly_chart(dashboard['monthly_performance'], use_container_width=True)
    except Exception as e:
        st.warning(f"Monthly visualization error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- AI COACH SECTION ---
    st.markdown('<div class="ai-analysis-box">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🤖 Decentralized AI Analysis</div>', unsafe_allow_html=True)
    
    col_ai_1, col_ai_2 = st.columns([1, 3])
    
    with col_ai_1:
        st.subheader("Analysis Settings")
        persona = st.selectbox(
            "Analysis Style", 
            ["Professional Performance Coach", "Ruthless Manager", "Supportive Coach", "Data Scientist", "Veteran Mentor"]
        )
        
        # Show current connection info
        current_config = st.session_state.get('ai_config', {})
        config_type = current_config.get('type', 'Not configured')
        type_labels = {
            'cloud_shared': 'Community Cloud',
            'local_tunnel': 'Local GPU', 
            'personal_api': 'Personal API'
        }
        
        st.info(f"**Compute:** {type_labels.get(config_type, 'Not configured')}")
        
        # Save Session Button
        if st.button("💾 Save Session", use_container_width=True):
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "total_trades": len(df),
                "total_pnl": float(total_pnl),
                "win_rate": float(win_rate),
                "compute_mode": config_type,
                "last_trade_date": str(df['Date'].iloc[-1]) if len(df) > 0 else None
            }
            
            json_str = json.dumps(session_data, indent=2)
            b64 = base64.b64encode(json_str.encode()).decode()
            href = f'<a href="data:file/json;base64,{b64}" download="trade_session.json">📥 Download Session</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.toast("Session saved to JSON!")

    with col_ai_2:
        st.subheader("Performance Insights")
        
        if st.button("🚀 Generate AI Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing your trading performance..."):
                # Prepare smart extraction prompt
                prompt = f"""
                Analyze this trader's performance comprehensively:
                
                Key Metrics:
                - Total P&L: ₹{total_pnl:,.2f}
                - Win Rate: {win_rate:.1f}%
                - Total Trades: {len(df)}
                - Best Trading Day: {best_day} (₹{best_day_pnl:,.2f})
                - Worst Trading Day: {worst_day} (₹{worst_day_pnl:,.2f})
                
                Performance Context:
                - Data covers period from {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}
                - Trades are chronologically ordered (auto-sorted timeline)
                
                Please provide:
                1. Overall performance assessment
                2. Key strengths and positive patterns
                3. Areas needing improvement
                4. Risk management observations
                5. Actionable trading recommendations
                6. Psychological insights
                """
                
                # Get AI analysis using decentralized router
                try:
                    insight = get_analysis(prompt, st.session_state.ai_config)
                    
                    # Display the insight
                    st.markdown(f"""
                    <div style="background-color: #262730; padding: 20px; border-radius: 10px; border-left: 4px solid #00ff00;">
                    <h4>AI Analysis</h4>
                    <p>{insight}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ AI Analysis failed: {str(e)}")
        
        # Quick Stats Summary
        st.markdown("### Quick Overview")
        st.info(f"""
        📊 **{len(df)}** total trades analyzed
        💰 **₹{abs(total_pnl):,.2f}** {'profit' if total_pnl >= 0 else 'loss'} overall
        🎯 **{win_rate:.1f}%** win rate achieved
        ⚡ Powered by **{type_labels.get(config_type, 'Unknown')}** compute
        """)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- DATA PREVIEW ---
    with st.expander("🔍 Raw Data Preview"):
        st.dataframe(df.head(10), use_container_width=True)
        st.caption(f"Showing first 10 of {len(df)} records")

# --- FOOTER ---
st.divider()
st.caption("📊 TradeMirror Pro - Decentralized AI Trading Analytics | Zero Permanent Storage | Your Data, Your Compute")