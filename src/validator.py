import pandas as pd
from src.database import get_ohlcv, get_existing_tickers, init_database



def validate_ticker(ticker):
    """
    Runs all validation checks on a single ticker.
    
    Args:
        ticker: Stock symbol to validate
        
    Returns:
        dict with validation results
    """
    df = get_ohlcv(ticker)
    
    results = {
        "ticker": ticker,
        "total_rows": len(df),
        "issues": []
    }
    
    # Enough data
    if len(df) < 2000:  # ~8 years of trading days
        results["issues"].append(f"Low row count: {len(df)} (expected ~2500)")
    
    # No negative prices
    price_columns = ["open", "high", "low", "close"]
    for col in price_columns:
        negatives = (df[col] < 0).sum()
        if negatives > 0:
            results["issues"].append(f"Negative values in {col}: {negatives} rows")
    
    # High should be higher than lower
    invalid_hl = (df["high"] < df["low"]).sum()
    if invalid_hl > 0:
        results["issues"].append(f"High < Low in {invalid_hl} rows")
    
    # No zero volume days
    zero_volume = (df["volume"] == 0).sum()
    if zero_volume > 0:
        results["issues"].append(f"Zero volume days: {zero_volume}")
    
    return results



def validate_all_tickers(verbose=False):
    """
    Validates all tickers in the database.
    
    Args:
        verbose: If True, print progress for each ticker
        
    Returns:
        dict with summary and list of tickers with issues
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
    
    # Summary statistics
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
    
