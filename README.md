# NSE Real-Time Momentum Dashboard

A high-performance, premium Streamlit dashboard for monitoring real-time momentum in NSE (National Stock Exchange) stocks. This tool scans the entire NSE EQUITY_L list to identify significant price movements based on user-defined thresholds and timeframes.

## 🚀 Features

- **Hybrid Momentum Logic**:
  - **Interval Mode**: Track % change over specific windows (5m, 15m, 1h, 2h, 3h, 4h, or custom up to 6h 15m).
  - **Open Price Mode**: Track % change relative to today's fixed market opening price.
- **Complete NSE Coverage**: Automatically fetches and scans 2000+ symbols from the latest NSE EQUITY_L list.
- **Premium UI/UX**:
  - **Dual Controls**: Synchronized sliders and precision buttons for all settings.
  - **Quick Intervals**: One-click presets for common trading timeframes.
  - **Categorized Display**: Stocks grouped by price ranges (₹0-50, ₹100-200, etc.) in clean, high-contrast metric cards.
- **Market Aware**:
  - **Market Hours Validation**: Automatically detects NSE trading hours (9:15 AM - 3:30 PM IST).
  - **Status Indicator**: Visual feedback on whether the market is currently open or closed.
- **Performance Optimized**: Uses asynchronous `yahooquery` batch processing to handle thousands of stocks in seconds.
- **Manual Scan Control**: Full control over data fetching to optimize bandwidth and focus.

## 🛠 Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) with custom Vanilla CSS.
- **Data Engine**: [yahooquery](https://github.com/dpguthrie/yahooquery) (asynchronous Finance API).
- **Data Logic**: [Pandas](https://pandas.pydata.org/) for vectorised calculations.
- **Environment**: Python 3.9+.

## ⚙️ Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "Trading view"
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Dashboard**:
   ```bash
   streamlit run app.py
   ```

## 📊 Usage Guide

1. **Set your Filters**: Select the price ranges you are interested in from the sidebar.
2. **Choose Logic**: Decide whether you want to see momentum relative to the **Day Open** or a **Moving Window** (e.g., last 15 mins).
3. **Adjust Threshold**: Set the minimum percentage change you want to track (e.g., ±2.0%).
4. **Scan**: Click **"Force Global Scan"** to pull the latest market data.
5. **Analyze**: Results are grouped by price range, with gainers and losers clearly marked with `+` and `–` signs.

---

*Note: This tool is for educational and informational purposes only. Trading involves risk.*
