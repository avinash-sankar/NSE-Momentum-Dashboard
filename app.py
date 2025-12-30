import streamlit as st
import pandas as pd
import time
from data_manager import get_nse_symbols, fetch_stock_changes, get_symbols_in_price_ranges

# Page configuration
st.set_page_config(
    page_title="Equity Momentum Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto"
)

# Custom CSS for Premium Look and Button Visibility
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 10px 0;
    }
    
    .section-header {
        color: #ff4b4b;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 20px;
        font-size: 1.4rem;
        border-left: 5px solid #ff4b4b;
        padding-left: 15px;
    }

    /* Fixed Button Styling for Visibility */
    .stButton>button {
        width: 100%;
        color: white !important;
        background-color: #262730;
        border: 1px solid #ff4b4b;
        font-weight: 700 !important;
        font-size: 1.2rem !important;
        height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: -10px; /* Bring closer to slider */
    }
    
    .stButton>button:hover {
        background-color: #ff4b4b;
        color: white !important;
    }
    
    /* Ensure sidebar is clean */
    [data-testid="stSidebar"] {
        padding-top: 20px;
    }
    
    /* Improve slider labels */
    .stSlider label {
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }

    /* Media Queries for Android/Mobile Optimization */
    @media (max-width: 768px) {
        .stTitle { font-size: 1.8rem !important; }
        .stSubheader { font-size: 1.1rem !important; }
        
        /* Larger touch targets for +/- and Preset buttons in sidebar */
        [data-testid="stSidebar"] button {
            height: 50px !important;
            font-size: 1.1rem !important;
        }
        
        /* Adjust metric cards for vertical stacking and readability */
        [data-testid="stMetric"] {
            padding: 15px !important;
            margin-bottom: 8px !important;
        }
        
        /* Make sidebar checkboxes easier to click */
        [data-testid="stSidebar"] div[data-testid="stCheckbox"] label {
            padding: 10px 0 !important;
            font-size: 1.1rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Session State for Dynamic Controls
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 10
if 'threshold' not in st.session_state:
    st.session_state.threshold = 5.0

# Sidebar
st.sidebar.title("🛠 Dashboard Settings")

# 0. Momentum Calculation Method

# 1. Price Range Filters
st.sidebar.markdown("### 💰 Price Ranges")
price_ranges_options = ['0-50', '50-100', '100-200', '200-300', '300-400', '400-500', '500-600', 'Above 600']
selected_ranges = []
for r in price_ranges_options:
    if st.sidebar.checkbox(f"₹{r}", value=(r in ['100-200', '200-300', '300-400'])):
        selected_ranges.append(r)

st.sidebar.markdown("---")

# 2. Synchronized Refresh Interval Controls
st.sidebar.markdown("### 🧬 Momentum Logic")
use_open_price = st.sidebar.checkbox("Use Open Price", value=False, help="If checked, calculates change since market open. If unchecked, uses the refresh interval window.")

st.sidebar.markdown("### ⏱ Refresh Rate")

# Quick Timeframe Presets
st.sidebar.markdown("#### *Quick Intervals*")
time_frames = {
    "Last 5m": 5,
    "Last 15m": 15,
    "Last 1H": 60,
    "2 Hours": 120,
    "3 Hours": 180,
    "4 Hours": 240
}

preset_cols = st.sidebar.columns(2)
for i, (label, value) in enumerate(time_frames.items()):
    col = preset_cols[i % 2]
    # Checkbox acts as a button toggle
    if col.checkbox(label, value=(st.session_state.refresh_interval == value), key=f"preset_{value}"):
        if st.session_state.refresh_interval != value:
            st.session_state.refresh_interval = value
            st.rerun()

st.sidebar.markdown("---")

h, m = divmod(st.session_state.refresh_interval, 60)
time_display = f"{h}h {m}m" if h > 0 else f"{m}m"
st.sidebar.markdown(f"**Current Window: {time_display}**")

st.session_state.refresh_interval = st.sidebar.slider(
    "Interval (min)", 1, 375, st.session_state.refresh_interval, key="slider_refresh"
)
col1, col2 = st.sidebar.columns(2)
if col1.button("➖ ", key="dec_refresh"):
    st.session_state.refresh_interval = max(1, st.session_state.refresh_interval - 1)
    st.rerun()
if col2.button("➕ ", key="inc_refresh"):
    st.session_state.refresh_interval = min(375, st.session_state.refresh_interval + 1)
    st.rerun()

st.sidebar.markdown("---")

# 3. Synchronized Momentum Threshold Controls
st.sidebar.markdown("### 🚀 Momentum")
st.session_state.threshold = st.sidebar.slider(
    "Threshold (%)", 0.1, 15.0, st.session_state.threshold, step=0.1, key="slider_threshold"
)
col3, col4 = st.sidebar.columns(2)
if col3.button("➖  ", key="dec_threshold"):
    st.session_state.threshold = max(0.1, round(st.session_state.threshold - 0.5, 1))
    st.rerun()
if col4.button("➕  ", key="inc_threshold"):
    st.session_state.threshold = min(20.0, round(st.session_state.threshold + 0.5, 1))
    st.rerun()

st.sidebar.markdown("---")

# Manual scan only

# Fetch all symbols once
if 'all_symbols' not in st.session_state:
    with st.spinner("Fetching NSE stocks..."):
        st.session_state.all_symbols = get_nse_symbols()

title_suffix = "since market open" if use_open_price else f"over {time_display}"
st.title("📈 Equity Momentum Dashboard")
st.subheader(f"Scanning stocks for greater than {st.session_state.threshold} % change {title_suffix}")

# Trigger Scan logic
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = 0

force_refresh = st.sidebar.button("Force Global Scan", use_container_width=True)

# NSE Market Hours Check
from data_manager import is_market_open
market_status = is_market_open()

if not market_status:
    st.sidebar.warning("🌙 Market is CLOSED (NSE: 9:15-15:30 IST)")
    st.sidebar.info("💡 Showing data from the last available trading session.")
else:
    st.sidebar.success("☀️ Market is OPEN")

# Trigger scan on manual button click OR initial load
is_initial_load = 'momentum_stocks' not in st.session_state
if force_refresh or is_initial_load:
    if not selected_ranges:
        if force_refresh:
            st.warning("Please select at least one price range in the sidebar.")
    else:
        with st.spinner(f"Filtering {len(st.session_state.all_symbols)} stocks by price..."):
            # Step 1: Pre-filter symbols by price
            filtered_symbols = get_symbols_in_price_ranges(st.session_state.all_symbols, selected_ranges)
            
            if filtered_symbols:
                scan_mode_text = "vs Open" if use_open_price else f"{time_display} Window"
                with st.spinner(f"Calculating momentum ({scan_mode_text}) for {len(filtered_symbols)} stocks..."):
                    # Step 2: Fetch momentum for filtered symbols only
                    st.session_state.momentum_stocks = fetch_stock_changes(
                        filtered_symbols, 
                        st.session_state.threshold,
                        window_mins=st.session_state.refresh_interval,
                        use_open_price=use_open_price
                    )
            else:
                st.session_state.momentum_stocks = []
                
        st.session_state.last_refresh = time.time()

# Display logic
if 'momentum_stocks' in st.session_state and st.session_state.momentum_stocks:
    stocks = st.session_state.momentum_stocks
    
    # Render selected categories
    for cat_name in selected_ranges:
        # Filter stocks falling into this specific category for grouping
        cat_stocks = []
        for s in stocks:
            p = s['Price']
            if cat_name == '0-50' and 0 <= p <= 50: cat_stocks.append(s)
            elif cat_name == '50-100' and 50 < p <= 100: cat_stocks.append(s)
            elif cat_name == '100-200' and 100 < p <= 200: cat_stocks.append(s)
            elif cat_name == '200-300' and 200 < p <= 300: cat_stocks.append(s)
            elif cat_name == '300-400' and 300 < p <= 400: cat_stocks.append(s)
            elif cat_name == '400-500' and 400 < p <= 500: cat_stocks.append(s)
            elif cat_name == '500-600' and 500 < p <= 600: cat_stocks.append(s)
            elif cat_name == 'Above 600' and p > 600: cat_stocks.append(s)
            
        if cat_stocks:
            st.markdown(f'<div class="section-header">₹{cat_name}</div>', unsafe_allow_html=True)
            cols = st.columns(4)
            for i, stock in enumerate(cat_stocks):
                with cols[i % 4]:
                    st.metric(
                        label=stock['Symbol'],
                        value=f"₹{stock['Price']}",
                        delta=f"{'+' if stock['Change %'] > 0 else ''}{stock['Change %']}%"
                    )
else:
    if selected_ranges:
        st.info("No momentum stocks found in the selected price ranges.")

# Footer
st.markdown("---")
st.caption(f"Last Scan: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_refresh))}. Manual refresh required.")
