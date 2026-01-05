# Algorithmic Trading Backtesting Engine

A Python-based backtesting engine for testing trading strategies on S&P 500 stocks using historical data.

## Overview

This project downloads 10 years of historical stock data for all S&P 500 companies, stores it in a SQLite database, and allows you to backtest various trading strategies to compare their performance.

## Features

- **Data Pipeline**: Automatically scrapes the current S&P 500 ticker list from Wikipedia and downloads historical OHLCV data via yfinance
- **SQLite Storage**: Efficiently stores ~1.2 million rows of stock data in a local database
- **Data Validation**: Checks for missing data, price anomalies, and other quality issues
- **Multiple Strategies**: Implements and compares four trading strategies
- **Performance Metrics**: Calculates total return, annualized return, max drawdown, and win rate
- **Visualization**: Generates comparison charts using matplotlib

## Project Structure
```
backtesting_engine/
├── data/
│   └── market_data.db        # SQLite database with stock data
├── src/
│   ├── __init__.py
│   ├── tickers.py            # Fetches S&P 500 ticker list
│   ├── downloader.py         # Downloads data from yfinance
│   ├── database.py           # SQLite operations
│   ├── validator.py          # Data quality checks
│   └── backtester.py         # Portfolio, strategies, and metrics
├── main.py                   # Main application entry point
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JojoKrueger/algorithmic-trading-backtesting-engine.git
cd algorithmic-trading-backtesting-engine
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:
```bash
python main.py
```

You'll see a menu with four options:

1. **Download S&P 500 data** - Downloads historical data for all S&P 500 stocks
2. **Validate data** - Checks data quality and reports issues
3. **Run backtest** - Compare trading strategies on a specific stock
4. **Exit**

### Example Backtest
```
==================================================
Backtesting
==================================================
Enter ticker symbol (e.g., AAPL): NVDA
Start date (YYYY-MM-DD): 2020-01-01
End date (YYYY-MM-DD): 2023-12-31

Strategy                       Return       Annual        MaxDD     Trades    WinRate
-------------------------------------------------------------------------------------
buy_and_hold                  728.58%       69.84%      -66.33%          2     100.0%
simple_moving_average         579.36%        61.6%      -42.66%         98     32.65%
rsi                           112.44%       20.77%      -35.63%         20      80.0%
macd                          220.57%       33.89%      -52.15%         80      42.5%
```

## Trading Strategies

### 1. Buy and Hold
The simplest strategy - buy on day one, sell on the last day. This serves as the baseline for comparison.

### 2. Simple Moving Average (SMA)
- **Buy signal**: Price crosses above 20-day moving average
- **Sell signal**: Price crosses below 20-day moving average
- **Philosophy**: Trend following

### 3. RSI (Relative Strength Index)
- **Buy signal**: RSI drops below 30 (oversold)
- **Sell signal**: RSI rises above 70 (overbought)
- **Philosophy**: Mean reversion

### 4. MACD (Moving Average Convergence Divergence)
- **Buy signal**: MACD line crosses above signal line
- **Sell signal**: MACD line crosses below signal line
- **Philosophy**: Momentum detection

## Performance Metrics

| Metric | Description |
|--------|-------------|
| Total Return | Overall percentage gain/loss |
| Annual Return | Compound annual growth rate (CAGR) |
| Max Drawdown | Largest peak-to-trough decline |
| Trades | Number of buy/sell transactions |
| Win Rate | Percentage of profitable round trips |

## Key Findings

After testing multiple strategies across different stocks and time periods:

1. **Buy and Hold consistently outperforms** timing strategies in bull markets
2. **Max drawdown matters** - Buy and Hold had the highest returns but also the largest drops (-66%)
3. **Win rate is misleading** - RSI had 80% win rate but lowest returns (small wins, missed big moves)
4. **No strategy wins everywhere** - Results vary by stock and market conditions

## Technologies Used

- **Python 3.x**
- **pandas** - Data manipulation
- **NumPy** - Numerical operations
- **yfinance** - Yahoo Finance API
- **SQLite** - Database storage
- **matplotlib** - Visualization
- **BeautifulSoup** - Web scraping
- **requests** - HTTP requests

## Future Enhancements

- [ ] Position sizing (partial buys/sells)
- [ ] Transaction costs and slippage
- [ ] More strategies (Bollinger Bands, momentum, etc.)
- [ ] Multi-stock portfolio backtesting
- [ ] Risk-adjusted metrics (Sharpe ratio, Sortino ratio)
- [ ] Interactive web dashboard

## License

MIT License

## Author

Johannes Krüger

## Disclaimer

This README was partly created by AI. I wrote the code in this project on my own and used AI as an assistance.