import yfinance as yf
from datetime import datetime, timedelta
from src.database import insert_ohlcv, get_existing_tickers, init_database


def download_ticker(ticker, years=10):
    """
    Downloads historical OHLCV data for a single ticker.
    
    Args:
        ticker: Stock symbol (e.g., "AAPL")
        years: How many years of history to download (default: 10)
    
    Returns:
        DataFrame with OHLCV data, or None if download failed
    """
   # Convert to yfinance format
    yf_ticker = clean_ticker(ticker)
   
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    print(f"Downloading {ticker}...")
    
    try:
        # Download from Yahoo Finance
        stock = yf.Ticker(yf_ticker)
        # Automatically gets the stock data as a Pandas Data Frame
        df = stock.history(start=start_date, end=end_date)
        
        # Check if we got data
        if df.empty:
            print(f"  No data returned for {ticker}")
            return None
        
        # Convert index (Date) to a regular column
        df = df.reset_index()
        
        # Clean up the date column - remove timezone and keep just the date
        df["Date"] = df["Date"].dt.date
        
        print(f"  Downloaded {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"  Error downloading {ticker}: {e}")
        return None

def download_all_tickers(tickers, years=10, skip_existing=True):
    """
    Downloads data for multiple tickers and stores in database.
    
    Args:
        tickers: List of stock symbols
        years: How many years of history to download (Default: 10)
        skip_existing: If True, skip tickers already in database
    """
    # Make sure database exists
    init_database()
    
    # Check what we already have
    if skip_existing:
        existing = get_existing_tickers()
        tickers_to_download = []
        for t in tickers:
            if t not in existing:
                tickers_to_download.append(t)
        print(f"Skipping {len(existing)} tickers already in database")
    else:
        tickers_to_download = tickers
    
    print(f"Downloading {len(tickers_to_download)} tickers...")
    
    # Download each ticker
    successful = 0
    failed = 0
    
    for ticker in tickers_to_download:
        df = download_ticker(ticker, years)
        
        if df is not None:
            insert_ohlcv(df, ticker)
            successful += 1
        else:
            failed += 1
    
    print(f"\nComplete! Downloaded {successful} tickers, {failed} failed")

def clean_ticker(ticker):
    """
    Converts ticker symbols to yfinance format.
    
    Some tickers use '.' on Wikipedia but '-' on Yahoo Finance.
    """
    return ticker.replace(".", "-")
    
if __name__ == "__main__":
    # Test with just 3 tickers first
    test_tickers = ["AAPL", "MSFT", "GOOGL"]
    download_all_tickers(test_tickers)
