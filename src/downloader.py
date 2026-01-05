import yfinance as yf
from datetime import datetime, timedelta
from src.database import insert_ohlcv, get_existing_tickers, init_database


def download_ticker(ticker, years=10):
    """
    Download historical market data for a single ticker using Yahoo Finance.
    """
    # Normalize ticker symbol for Yahoo Finance
    yf_ticker = clean_ticker(ticker)
   
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    
    print(f"Downloading {ticker}...")
    
    try:
        stock = yf.Ticker(yf_ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"  No data returned for {ticker}")
            return None
        
        # Flatten index and normalize date format for storage
        df = df.reset_index()
        df["Date"] = df["Date"].dt.date
        
        print(f"  Downloaded {len(df)} rows")
        return df
        
    except Exception as e:
        print(f"  Error downloading {ticker}: {e}")
        return None


def download_all_tickers(tickers, years=10, skip_existing=True):
    """
    Download and persist market data for a list of tickers.
    """
    init_database()
    
    if skip_existing:
        existing = get_existing_tickers()
        tickers_to_download = [t for t in tickers if t not in existing]
        print(f"Skipping {len(existing)} tickers already in database")
    else:
        tickers_to_download = tickers
    
    print(f"Downloading {len(tickers_to_download)} tickers...")
    
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
    Convert ticker symbols to Yahoo Finance-compatible format.
    """
    return ticker.replace(".", "-")


if __name__ == "__main__":
    test_tickers = ["AAPL", "MSFT", "GOOGL"]
    download_all_tickers(test_tickers)
