import pandas as pd
from src.database import get_ohlcv, get_existing_tickers, init_database


def validate_ticker(ticker):
    """
    Run basic data integrity checks for a single ticker.
    """
    df = get_ohlcv(ticker)
    
    results = {
        "ticker": ticker,
        "total_rows": len(df),
        "issues": []
    }
    
    # Verify we have a reasonable amount of historical data
    if len(df) < 2000:  # roughly 8 years of trading days
        results["issues"].append(f"Low row count: {len(df)} (expected ~2500)")
    
    # Prices should never be negative
    price_columns = ["open", "high", "low", "close"]
    for col in price_columns:
        negatives = (df[col] < 0).sum()
        if negatives > 0:
            results["issues"].append(f"Negative values in {col}: {negatives} rows")
    
    # High should always be greater than or equal to low
    invalid_hl = (df["high"] < df["low"]).sum()
    if invalid_hl > 0:
        results["issues"].append(f"High < Low in {invalid_hl} rows")
    
    # Volume should be positive on all trading days
    zero_volume = (df["volume"] == 0).sum()
    if zero_volume > 0:
        results["issues"].append(f"Zero volume days: {zero_volume}")
    
    return results


def validate_all_tickers(verbose=False):
    """
    Run validation checks across all tickers in the database.
    """
    tickers = get_existing_tickers()
    
    all_results = []
    tickers_with_issues = []
    
    print(f"Validating {len(tickers)} tickers...")
    
    for ticker in tickers:
        result = validate_ticker(ticker)
        all_results.append(result)
        
        if result["issues"]:
            tickers_with_issues.append(result)
            if verbose:
                print(f"  {ticker}: {result['issues']}")
    
    summary = {
        "total_tickers": len(tickers),
        "tickers_with_issues": len(tickers_with_issues),
        "problem_tickers": tickers_with_issues
    }
    
    return summary


if __name__ == "__main__":
    summary = validate_all_tickers(verbose=True)
    
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Total tickers: {summary['total_tickers']}")
    print(f"Tickers with issues: {summary['tickers_with_issues']}")
