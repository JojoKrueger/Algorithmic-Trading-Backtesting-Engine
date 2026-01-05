import pandas as pd
from src.database import get_ohlcv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class Portfolio:
    """
    Tracks cash, shares, and portfolio value during backtesting.
    """
    
    def __init__(self, starting_cash):
        """
        Initialize portfolio with cash, no shares.
        
        Args:
            starting_cash: Amount of money to start with (e.g., 10000)
        """
        self.cash = starting_cash
        self.shares = 0
        self.starting_cash = starting_cash
    
    def buy(self, price, quantity=None):
        """
        Buy shares at the given price.
        
        Args:
            price: Price per share
            quantity: Number of shares to buy (if None, buy as many as possible)
        
        Returns:
            Number of shares actually bought
        """
        if quantity is None:
            # Buy as many as we can afford
            quantity = int(self.cash // price)
        
        cost = price * quantity
        
        if cost > self.cash:
            print(f"Not enough cash. Have ${self.cash:.2f}, need ${cost:.2f}")
            return 0
        
        self.cash -= cost
        self.shares += quantity
        
        return quantity
    
    def sell(self, price, quantity=None):
        """
        Sell shares at the given price.
        
        Args:
            price: Price per share
            quantity: Number of shares to sell (if None, sell all)
        
        Returns:
            Number of shares actually sold
        """
        if quantity is None:
            # Sell everything
            quantity = self.shares
        
        if quantity > self.shares:
            print(f"Not enough shares. Have {self.shares}, trying to sell {quantity}")
            return 0
        
        revenue = price * quantity
        
        self.cash += revenue
        self.shares -= quantity
        
        return quantity
    
    def total_value(self, current_price):
        """
        Calculate total portfolio value at current price.
        
        Args:
            current_price: Current price per share
        
        Returns:
            Total value (cash + shares * price)
        """
        return self.cash + (self.shares * current_price)


def generate_signals(df, strategy="buy_and_hold"):
    """
    Generates buy/sell signals based on a strategy.
    
    Args:
        df: DataFrame with OHLCV data
        strategy: Strategy name
    
    Returns:
        DataFrame with added 'signal' column (1 = buy, -1 = sell, 0 = hold)
    """
    df = df.copy()
    df["signal"] = 0  # Default: hold
    
    if strategy == "buy_and_hold":
        df.iloc[0, df.columns.get_loc("signal")] = 1   # Buy first day
        df.iloc[-1, df.columns.get_loc("signal")] = -1  # Sell last day
    
    elif strategy == "simple_moving_average":
        # Buy when price crosses above 20-day average
        # Sell when price crosses below 20-day average
        window = 20
        df["sma"] = df["close"].rolling(window=window).mean()
        
        for i in range(window, len(df)): # from 20 to 1000 if we have 1000 days of data
            price = df.iloc[i]["close"] # current closing price (can use easy .iloc because we READ)
            sma = df.iloc[i]["sma"] # sma for this day
            prev_price = df.iloc[i-1]["close"] # previous day closing price
            prev_sma = df.iloc[i-1]["sma"] # previous day sma 
            
            # Price crosses above SMA → Buy
            if prev_price <= prev_sma and price > sma:
                df.iloc[i, df.columns.get_loc("signal")] = 1 # df.iloc[row_number, column_number] (need specify beacuse we WRITE)
            # Price crosses below SMA → Sell
            elif prev_price >= prev_sma and price < sma:
                df.iloc[i, df.columns.get_loc("signal")] = -1
    
    elif strategy == "rsi":
        # RSI parameters
        period = 14
        oversold = 30
        overbought = 70
        
        # Calculate daily price changes
        delta = df["close"].diff()
        
        # Separate gains and losses
        gains = delta.copy()
        losses = delta.copy()
        gains[gains < 0] = 0      # Keep only positive values
        losses[losses > 0] = 0    # Keep only negative values
        losses = abs(losses)      # Make losses positive for calculation
        
        # Calculate average gain and loss over the period
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # Generate signals
        for i in range(period, len(df)):
            rsi = df.iloc[i]["rsi"]
            prev_rsi = df.iloc[i-1]["rsi"]
            
            # RSI crosses below oversold → Buy
            if prev_rsi >= oversold and rsi < oversold:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            # RSI crosses above overbought → Sell
            elif prev_rsi <= overbought and rsi > overbought:
                df.iloc[i, df.columns.get_loc("signal")] = -1
    
    elif strategy == "macd":
        # MACD parameters
        fast_period = 12
        slow_period = 26
        signal_period = 9
        
        # Calculate EMAs (Exponential Moving Averages)
        ema_fast = df["close"].ewm(span=fast_period, adjust=False).mean() # .ewm = exponential weighted moving: pandas build in method to simulate ema's 
        ema_slow = df["close"].ewm(span=slow_period, adjust=False).mean()
        
        # MACD line = fast EMA - slow EMA
        df["macd"] = ema_fast - ema_slow
        
        # Signal line = 9-day EMA of MACD
        df["macd_signal"] = df["macd"].ewm(span=signal_period, adjust=False).mean()
        
        # Generate signals
        start_idx = slow_period + signal_period  # Waiting for a couple of days to get stable ema's 
        
        for i in range(start_idx, len(df)):
            macd = df.iloc[i]["macd"]
            signal = df.iloc[i]["macd_signal"]
            prev_macd = df.iloc[i-1]["macd"]
            prev_signal = df.iloc[i-1]["macd_signal"]
            
            # MACD crosses above signal line → Buy
            if prev_macd <= prev_signal and macd > signal:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            # MACD crosses below signal line → Sell
            elif prev_macd >= prev_signal and macd < signal:
                df.iloc[i, df.columns.get_loc("signal")] = -1

    return df

def backtest_strategy(ticker, start_date, end_date, strategy="buy_and_hold", starting_cash=10000):
    """
    Backtest any strategy that generates signals. We simulate one portfolio with one stock.
    
    Args:
        ticker: Stock symbol
        start_date: Start date "YYYY-MM-DD"
        end_date: End date "YYYY-MM-DD"
        strategy: Strategy name ("buy_and_hold" or "simple_moving_average")
        starting_cash: Initial portfolio value
    
    Returns:
        dict with backtest results
    """
    # Get historical data
    df = get_ohlcv(ticker, start_date, end_date)
    
    if len(df) == 0:
        print(f"No data found for {ticker}")
        return None
    
    # Generate signals based on strategy
    df = generate_signals(df, strategy)
    
    # Create portfolio
    portfolio = Portfolio(starting_cash)
    
    # Track trades
    trades = []
    
    # Loop through each day
    for i in range(len(df)):
        row = df.iloc[i]
        signal = row["signal"]
        price = row["close"]
        date = row["date"]
        
        if signal == 1 and portfolio.shares == 0:  # Buy signal and not already holding
            shares = portfolio.buy(price)
            if shares > 0:
                trades.append({"date": date, "action": "BUY", "price": price, "shares": shares})
        
        elif signal == -1 and portfolio.shares > 0:  # Sell signal and holding shares
            shares = portfolio.sell(price)
            if shares > 0:
                trades.append({"date": date, "action": "SELL", "price": price, "shares": shares})
    
    # If still holding shares at the end, sell them
    if portfolio.shares > 0:
        final_price = df.iloc[-1]["close"]
        shares = portfolio.sell(final_price)
        trades.append({"date": df.iloc[-1]["date"], "action": "SELL (end)", "price": final_price, "shares": shares})
    
    # Calculate results
    total_return = (portfolio.cash - starting_cash) / starting_cash * 100
    
    results = {
        "ticker": ticker,
        "strategy": strategy,
        "start_date": df.iloc[0]["date"],
        "end_date": df.iloc[-1]["date"],
        "starting_cash": starting_cash,
        "ending_cash": round(portfolio.cash, 2),
        "total_return_pct": round(total_return, 2),
        "num_trades": len(trades),
        "trades": trades
    }
    
    return results


def calculate_metrics(ticker, start_date, end_date, strategy, starting_cash=10000):
    """
    Calculate detailed performance metrics for a strategy.
    
    Returns dict with:
        - total_return: Overall percentage gain/loss
        - annual_return: Annualized return
        - max_drawdown: Largest peak-to-trough decline
        - num_trades: Number of trades executed
        - win_rate: Percentage of profitable trades
    """
    # Get data and generate signals
    df = get_ohlcv(ticker, start_date, end_date)
    df = generate_signals(df, strategy)
    
    # Run backtest
    portfolio = Portfolio(starting_cash)
    trades = []
    portfolio_values = []  # Track value over time
    
    for i in range(len(df)):
        row = df.iloc[i]
        signal = row["signal"]
        price = row["close"]
        
        # Execute trades
        if signal == 1 and portfolio.shares == 0:
            shares = portfolio.buy(price)
            if shares > 0:
                trades.append({"action": "BUY", "price": price})
        elif signal == -1 and portfolio.shares > 0:
            shares = portfolio.sell(price)
            if shares > 0:
                trades.append({"action": "SELL", "price": price})
        
        # Record portfolio value
        portfolio_values.append(portfolio.total_value(price))
    
    # Sell remaining shares
    if portfolio.shares > 0:
        final_price = df.iloc[-1]["close"]
        portfolio.sell(final_price)
        trades.append({"action": "SELL", "price": final_price})
    
    # Calculate metrics (easier with np array)
    portfolio_values = np.array(portfolio_values)
    
    # Total return
    total_return = (portfolio.cash - starting_cash) / starting_cash * 100
    
    # Annualized return
    years = len(df) / 252  # 252 trading days per year
    if total_return > -100:  # Avoid math errors
        annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100
    else:
        annual_return = -100
    
    # Max drawdown (largest peak-to-trough decline)
    peak = np.maximum.accumulate(portfolio_values)
    drawdown = (portfolio_values - peak) / peak * 100
    max_drawdown = drawdown.min()
    
    # Win rate (percentage of profitable trades)
    if len(trades) >= 2:
        profits = []
        for j in range(0, len(trades) - 1, 2):  # Pair buys with sells
            if j + 1 < len(trades):
                buy_price = trades[j]["price"]
                sell_price = trades[j + 1]["price"]
                profits.append(sell_price > buy_price)
        win_rate = sum(profits) / len(profits) * 100 if profits else 0 #if we have profitable trades at all
    else:
        win_rate = 0
    
    return {
        "ticker": ticker,
        "strategy": strategy,
        "total_return": round(total_return, 2),
        "annual_return": round(annual_return, 2),
        "max_drawdown": round(max_drawdown, 2),
        "num_trades": len(trades),
        "win_rate": round(win_rate, 2),
        "portfolio_values": portfolio_values  # For plotting
    }




def plot_strategy_comparison(ticker, start_date, end_date, starting_cash=10000):
    """
    Plot portfolio value over time for all strategies.
    """
    strategies = ["buy_and_hold", "simple_moving_average", "rsi", "macd"]
    colors = ["blue", "green", "red", "purple"]
    
    # Get dates for x-axis
    df = get_ohlcv(ticker, start_date, end_date)
    dates = pd.to_datetime(df["date"])  # Convert to datetime objects
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for strategy, color in zip(strategies, colors):
        metrics = calculate_metrics(ticker, start_date, end_date, strategy, starting_cash)
        ax.plot(dates, metrics["portfolio_values"], label=strategy, color=color, linewidth=1)
    
    # Set x-axis limits to our actual date range
    ax.set_xlim(dates.iloc[0], dates.iloc[-1])
    
    # Format x-axis to show fewer dates
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))  # Every 6 months
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))   # Format: 2020-01
    plt.xticks(rotation=45)  # Rotate labels for readability
    
    # Formatting
    plt.title(f"Strategy Comparison: {ticker} ({start_date} to {end_date})")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save and show
    plt.savefig("strategy_comparison.png")
    plt.show()
    
    print("Chart saved as strategy_comparison.png")

if __name__ == "__main__":
    plot_strategy_comparison("NVDA", "2020-01-01", "2023-12-31")