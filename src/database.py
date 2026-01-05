import sqlite3
from pathlib import Path
import os

import pandas as pd


# Resolve database location based on runtime environment
# Streamlit Cloud does not allow writing to the project directory
if os.environ.get("STREAMLIT_SHARING_MODE") or os.path.exists("/mount/src"):
    DB_PATH = Path("/tmp/market_data.db")
else:
    DB_PATH = Path(__file__).parent.parent / "data" / "market_data.db"


def init_database():
    """
    Initialize the local SQLite database and create required tables
    if they do not already exist.
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
    Insert OHLCV data for a single ticker into the database.
    Assumes the input DataFrame follows a standard market data format.
    """
    data = df.copy()
    
    # Normalize schema to match database table
    data["ticker"] = ticker
    data = data.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    data = data[["ticker", "date", "open", "high", "low", "close", "volume"]]
    
    connection = sqlite3.connect(DB_PATH)
    data.to_sql("ohlcv", connection, if_exists="append", index=False)
    connection.close()
    
    print(f"Inserted {len(data)} rows for {ticker}")


def get_ohlcv(ticker, start_date=None, end_date=None):
    """
    Fetch OHLCV data for a ticker, optionally constrained by date range.
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
    Return all tickers currently present in the database.
    """
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute("SELECT DISTINCT ticker FROM ohlcv")
    results = cursor.fetchall()
    
    connection.close()
    
    return [row[0] for row in results]


if __name__ == "__main__":
    init_database()
    
    existing = get_existing_tickers()
    print(f"Tickers in database: {existing}")
