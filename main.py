from src.tickers import get_sp500_tickers
from src.downloader import download_all_tickers
from src.database import init_database, get_existing_tickers
from src.validator import validate_all_tickers
from src.backtester import backtest_strategy, calculate_metrics, plot_strategy_comparison
from datetime import datetime
from src.database import get_existing_tickers


def get_valid_ticker():
    """Prompt user for a valid ticker symbol."""
    existing_tickers = get_existing_tickers()
    
    while True:
        try:
            ticker = input("Enter ticker symbol (e.g., AAPL): ").upper()
        except EOFError:
            print("\nInput cancelled.")
            return None
        
        if ticker in existing_tickers:
            return ticker
        else:
            print(f"  '{ticker}' not found in database.")
            print(f"  Examples: {existing_tickers[:5]}")


def get_valid_date(prompt, after_date=None):
    """Prompt user for a valid date."""
    while True:
        try:
            date_str = input(prompt)
        except EOFError:
            print("\nInput cancelled.")
            return None, None
        
        # Check format
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("  Invalid format. Please use YYYY-MM-DD (e.g., 2020-01-01)")
            continue
        
        # Check if end date is after start date
        if after_date:
            if date_obj <= after_date:
                print(f"  End date must be after start date ({after_date.strftime('%Y-%m-%d')})")
                continue
        
        return date_str, date_obj


def run_backtest():
    """Run backtesting comparison."""
    print("=" * 50)
    print("Backtesting")
    print("=" * 50)
    
    # Get validated user input
    ticker = get_valid_ticker()
    if ticker is None:
        return
    
    start_date, start_obj = get_valid_date("Start date (YYYY-MM-DD): ")
    if start_date is None:
        return
    
    end_date, end_obj = get_valid_date("End date (YYYY-MM-DD): ", after_date=start_obj)
    if end_date is None:
        return
    
    strategies = ["buy_and_hold", "simple_moving_average", "rsi", "macd"]
    
    print(f"\n{'Strategy':<25} {'Return':>12} {'Annual':>12} {'MaxDD':>12} {'Trades':>10} {'WinRate':>10}")
    print("-" * 85)
    
    for strategy in strategies:
        m = calculate_metrics(ticker, start_date, end_date, strategy)
        if m:
            print(f"{strategy:<25} {m['total_return']:>11}% {m['annual_return']:>11}% {m['max_drawdown']:>11}% {m['num_trades']:>10} {m['win_rate']:>9}%")
    
    # Ask if user wants to see the chart
    try:
        response = input("\nShow comparison chart? (y/n): ")
    except EOFError:
        return
    
    if response.lower() == "y":
        plot_strategy_comparison(ticker, start_date, end_date)


def download_data():
    """Download S&P 500 historical data."""
    print("=" * 50)
    print("S&P 500 Data Pipeline")
    print("=" * 50)
    
    # Get the list of S&P 500 tickers
    print("\nFetching S&P 500 ticker list...")
    tickers = get_sp500_tickers()
    print(f"Found {len(tickers)} tickers")
    
    # Show current database status
    existing = get_existing_tickers()
    print(f"Already in database: {len(existing)} tickers")
    print(f"Remaining to download: {len(tickers) - len(existing)}")
    
    # Ask user to confirm before downloading
    response = input("\nStart download? (y/n): ")
    if response.lower() != "y":
        print("Aborted.")
        return
    
    # Download all tickers
    download_all_tickers(tickers, years=10)
    
    print("\nDownload complete!")


def validate_data():
    """Validate the downloaded data."""
    print("=" * 50)
    print("Data Validation")
    print("=" * 50)
    
    summary = validate_all_tickers(verbose=True)
    
    print(f"\nTotal tickers: {summary['total_tickers']}")
    print(f"Tickers with issues: {summary['tickers_with_issues']}")




def main():
    """Main menu."""
    init_database()
    
    while True:
        print("\n" + "=" * 50)
        print("ALGORITHMIC TRADING BACKTESTING ENGINE")
        print("=" * 50)
        print("1. Download S&P 500 data")
        print("2. Validate data")
        print("3. Run backtest")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ")
        
        if choice == "1":
            download_data()
        elif choice == "2":
            validate_data()
        elif choice == "3":
            run_backtest()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please enter 1-4.")


if __name__ == "__main__":
    main()