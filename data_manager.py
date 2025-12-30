from yahooquery import Ticker
import pandas as pd
import requests
import io
from datetime import datetime, time as dtime, timezone, timedelta

def is_market_open():
    """
    Checks if the NSE market is currently open (9:15 AM - 3:30 PM IST, Mon-Fri).
    """
    # UTC to IST conversion (UTC + 5:30)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = datetime.now(timezone.utc) + ist_offset
    
    # Weekday check: 0=Monday, 6=Sunday
    if now_ist.weekday() >= 5:
        return False
        
    current_time = now_ist.time()
    market_open = dtime(9, 15)
    market_close = dtime(15, 30)
    
    return market_open <= current_time <= market_close

def get_nse_symbols():
    """
    Fetches the complete list of stocks listed on NSE (EQUITY_L.csv).
    """
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # The column is 'SYMBOL' for the complete list
            symbols = df['SYMBOL'].tolist()
            return [f"{s}.NS" for s in symbols]
    except Exception as e:
        print(f"Error fetching symbols from NSE: {e}")
    
    # Fallback to a small list of top stocks if the URL fails or for testing
    return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"]

def get_symbols_in_price_ranges(symbols, selected_ranges):
    """
    Fetches current prices for all symbols and returns those matching selected ranges.
    Uses 'history' as it is currently more reliable than 'price'.
    """
    if not symbols or not selected_ranges:
        return []

    results = []
    batch_size = 200 # History is heavier, smaller batch
    
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        try:
            t = Ticker(batch, asynchronous=True)
            data = t.history(period='1d')
            
            if data.empty:
                continue
                
            for symbol, ticker_data in data.groupby(level=0):
                if not ticker_data.empty:
                    # Current price is the last 'close'
                    price = ticker_data['close'].iloc[-1]
                    
                    matched = False
                    if '0-50' in selected_ranges and 0 <= price <= 50: matched = True
                    elif '50-100' in selected_ranges and 50 < price <= 100: matched = True
                    elif '100-200' in selected_ranges and 100 < price <= 200: matched = True
                    elif '200-300' in selected_ranges and 200 < price <= 300: matched = True
                    elif '300-400' in selected_ranges and 300 < price <= 400: matched = True
                    elif '400-500' in selected_ranges and 400 < price <= 500: matched = True
                    elif '500-600' in selected_ranges and 500 < price <= 600: matched = True
                    elif 'Above 600' in selected_ranges and price > 600: matched = True
                    
                    if matched:
                        results.append(symbol)
        except Exception as e:
            print(f"Error pre-filtering batch: {e}")
            
    return results

def fetch_stock_changes(symbols, threshold=5.0, window_mins=15, use_open_price=False):
    """
    Calculates % change.
    If use_open_price is True: calculates (Current - Open) / Open.
    If use_open_price is False: calculates (Current - Price_X_min_ago) / Price_X_min_ago.
    """
    if not symbols:
        return []

    results = []
    
    if use_open_price:
        # Using 'history' as it is currently more reliable than 'price'
        batch_size = 200 
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            try:
                t = Ticker(batch, asynchronous=True)
                data = t.history(period='1d')
                if data.empty: continue
                
                for symbol, ticker_data in data.groupby(level=0):
                    if not ticker_data.empty:
                        opened = ticker_data['open'].iloc[0]
                        current = ticker_data['close'].iloc[-1]
                        
                        if pd.isna(current) or pd.isna(opened) or opened == 0: continue
                        pct_change = ((current - opened) / opened) * 100
                        if abs(pct_change) >= threshold:
                            results.append({
                                'Symbol': symbol.replace('.NS', ''),
                                'Price': round(float(current), 2),
                                'Change %': round(float(pct_change), 2)
                            })
            except Exception as e:
                print(f"Error fetching open-price batch: {e}")
    else:
        # Path for Window/Interval-based momentum
        batch_size = 100
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            try:
                t = Ticker(batch, asynchronous=True)
                data = t.history(period='1d', interval='1m')
                if data.empty: continue
                for symbol, ticker_data in data.groupby(level=0):
                    try:
                        ticker_data = ticker_data.dropna(subset=['close'])
                        if len(ticker_data) < 2: continue
                        current_price = ticker_data['close'].iloc[-1]
                        lookback_idx = -(window_mins + 1)
                        if len(ticker_data) >= abs(lookback_idx):
                            price_past = ticker_data['close'].iloc[lookback_idx]
                        else:
                            price_past = ticker_data['close'].iloc[0]
                        if pd.isna(current_price) or pd.isna(price_past) or price_past == 0: continue
                        pct_change = ((current_price - price_past) / price_past) * 100
                        if abs(pct_change) >= threshold:
                            results.append({
                                'Symbol': symbol.replace('.NS', ''),
                                'Price': round(float(current_price), 2),
                                'Change %': round(float(pct_change), 2)
                            })
                    except Exception: pass
            except Exception as e:
                print(f"Error downloading history batch: {e}")
            
    return results

if __name__ == "__main__":
    test_symbols = get_nse_symbols()[:50]
    print("Testing Interval-based (Default)...")
    print(fetch_stock_changes(test_symbols, threshold=0.1, window_mins=10, use_open_price=False)[:2])
    print("Testing Open-based...")
    print(fetch_stock_changes(test_symbols, threshold=0.1, use_open_price=True)[:2])
