import sqlite3
from pathlib import Path

import pandas as pd

# Database file location
DB_PATH = Path(__file__).parent.parent / "data" / "market_data.db"


def init_database():
    """
    Creates the OHLCV table if it doesn't already exist.
    
    This is safe to call multiple times - it won't destroy existing data.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv (
            ticker TEXT,
            date DATE,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, date)
        )
    """)
    
    connection.commit()
    connection.close()
    
    print(f"Database initialized at {DB_PATH}")


def insert_ohlcv(df, ticker):
    """
    Inserts OHLCV data for a single ticker into the database.
    
    Args:
        df: DataFrame with columns: Date, Open, High, Low, Close, Volume
        ticker: Stock symbol (e.g., "AAPL")
    """
    # Make a copy so we don't modify the original
    data = df.copy()
    
    # Add the ticker column
    data["ticker"] = ticker
    
    # Rename columns to match our database schema
    data = data.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    # Keep only the columns we need, in the right order
    data = data[["ticker", "date", "open", "high", "low", "close", "volume"]]
    
    # Insert into database
    connection = sqlite3.connect(DB_PATH)
    data.to_sql("ohlcv", connection, if_exists="append", index=False)
    connection.close()
    
    print(f"Inserted {len(data)} rows for {ticker}")


def get_ohlcv(ticker, start_date=None, end_date=None):
    """
    Retrieves OHLCV data for a ticker from the database.
    
    Args:
        ticker: Stock symbol (e.g., "AAPL")
        start_date: Optional start date (string: "YYYY-MM-DD")
        end_date: Optional end date (string: "YYYY-MM-DD")
    
    Returns:
        DataFrame with the requested data
    """
    connection = sqlite3.connect(DB_PATH)
    
    query = "SELECT * FROM ohlcv WHERE ticker = ?"
    params = [ticker]
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date"
    
    df = pd.read_sql(query, connection, params=params)
    connection.close()
    
    return df


def get_existing_tickers():
    """
    Returns a list of tickers that already have data in the database.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute("SELECT DISTINCT ticker FROM ohlcv")
    results = cursor.fetchall()
    
    connection.close()
    
    # fetchall returns list of tuples: [("AAPL",), ("MSFT",), ...]
    # We extract just the ticker strings
    return [row[0] for row in results]


if __name__ == "__main__":
    init_database()
    
    existing = get_existing_tickers()
    print(f"Tickers in database: {existing}")