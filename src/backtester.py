import pandas as pd
from src.database import get_ohlcv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class Portfolio:
    """
    Simple portfolio model for single-asset backtesting.
    Tracks cash and share holdings over time.
    """
    
    def __init__(self, starting_cash):
        self.cash = starting_cash
        self.shares = 0
        self.starting_cash = starting_cash
    
    def buy(self, price, quantity=None):
        """
        Execute a buy order at the given price.
        If quantity is not specified, invest all available cash.
        """
        if quantity is None:
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
        Execute a sell order at the given price.
        If quantity is not specified, sell the full position.
        """
        if quantity is None:
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
        Current portfolio value using the given market price.
        """
        return self.cash + (self.shares * current_price)


def generate_signals(df, strategy="buy_and_hold"):
    """
    Generate trading signals for a given strategy.
    signal:  1 = buy, -1 = sell, 0 = hold
    """
    df = df.copy()
    df["signal"] = 0
    
    if strategy == "buy_and_hold":
        # Enter on the first day, exit on the last
        df.iloc[0, df.columns.get_loc("signal")] = 1
        df.iloc[-1, df.columns.get_loc("signal")] = -1
    
    elif strategy == "simple_moving_average":
        window = 20
        df["sma"] = df["close"].rolling(window=window).mean()
        
        # Detect price/SMA crossovers
        for i in range(window, len(df)):
            price = df.iloc[i]["close"]
            sma = df.iloc[i]["sma"]
            prev_price = df.iloc[i - 1]["close"]
            prev_sma = df.iloc[i - 1]["sma"]
            
            if prev_price <= prev_sma and price > sma:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            elif prev_price >= prev_sma and price < sma:
                df.iloc[i, df.columns.get_loc("signal")] = -1
    
    elif strategy == "rsi":
        period = 14
        oversold = 30
        overbought = 70
        
        delta = df["close"].diff()
        
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))
        
        # Look for RSI threshold crossings
        for i in range(period, len(df)):
            rsi = df.iloc[i]["rsi"]
            prev_rsi = df.iloc[i - 1]["rsi"]
            
            if prev_rsi >= oversold and rsi < oversold:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            elif prev_rsi <= overbought and rsi > overbought:
                df.iloc[i, df.columns.get_loc("signal")] = -1
    
    elif strategy == "macd":
        fast_period = 12
        slow_period = 26
        signal_period = 9
        
        ema_fast = df["close"].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow_period, adjust=False).mean()
        
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=signal_period, adjust=False).mean()
        
        # Skip early rows where EMAs are still stabilizing
        start_idx = slow_period + signal_period
        
        for i in range(start_idx, len(df)):
            macd = df.iloc[i]["macd"]
            signal = df.iloc[i]["macd_signal"]
            prev_macd = df.iloc[i - 1]["macd"]
            prev_signal = df.iloc[i - 1]["macd_signal"]
            
            if prev_macd <= prev_signal and macd > signal:
                df.iloc[i, df.columns.get_loc("signal")] = 1
            elif prev_macd >= prev_signal and macd < signal:
                df.iloc[i, df.columns.get_loc("signal")] = -1

    return df


def backtest_strategy(ticker, start_date, end_date, strategy="buy_and_hold", starting_cash=10000):
    """
    Run a single-asset backtest using the specified strategy.
    """
    df = get_ohlcv(ticker, start_date, end_date)
    
    if df.empty:
        print(f"No data found for {ticker}")
        return None
    
    df = generate_signals(df, strategy)
    portfolio = Portfolio(starting_cash)
    trades = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        signal = row["signal"]
        price = row["close"]
        date = row["date"]
        
        if signal == 1 and portfolio.shares == 0:
            shares = portfolio.buy(price)
            if shares:
                trades.append({"date": date, "action": "BUY", "price": price, "shares": shares})
        
        elif signal == -1 and portfolio.shares > 0:
            shares = portfolio.sell(price)
            if shares:
                trades.append({"date": date, "action": "SELL", "price": price, "shares": shares})
    
    # Close any open position at the end of the test
    if portfolio.shares > 0:
        final_price = df.iloc[-1]["close"]
        shares = portfolio.sell(final_price)
        trades.append({
            "date": df.iloc[-1]["date"],
            "action": "SELL (end)",
            "price": final_price,
            "shares": shares
        })
    
    total_return = (portfolio.cash - starting_cash) / starting_cash * 100
    
    return {
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


def calculate_metrics(ticker, start_date, end_date, strategy, starting_cash=10000):
    """
    Compute performance metrics for a backtested strategy.
    """
    df = get_ohlcv(ticker, start_date, end_date)
    df = generate_signals(df, strategy)
    
    portfolio = Portfolio(starting_cash)
    trades = []
    portfolio_values = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        signal = row["signal"]
        price = row["close"]
        
        if signal == 1 and portfolio.shares == 0:
            shares = portfolio.buy(price)
            if shares:
                trades.append({"action": "BUY", "price": price})
        
        elif signal == -1 and portfolio.shares > 0:
            shares = portfolio.sell(price)
            if shares:
                trades.append({"action": "SELL", "price": price})
        
        portfolio_values.append(portfolio.total_value(price))
    
    if portfolio.shares > 0:
        final_price = df.iloc[-1]["close"]
        portfolio.sell(final_price)
        trades.append({"action": "SELL", "price": final_price})
    
    portfolio_values = np.array(portfolio_values)
    
    total_return = (portfolio.cash - starting_cash) / starting_cash * 100
    
    years = len(df) / 252
    annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if total_return > -100 else -100
    
    peak = np.maximum.accumulate(portfolio_values)
    drawdown = (portfolio_values - peak) / peak * 100
    max_drawdown = drawdown.min()
    
    if len(trades) >= 2:
        profits = []
        for i in range(0, len(trades) - 1, 2):
            profits.append(trades[i + 1]["price"] > trades[i]["price"])
        win_rate = sum(profits) / len(profits) * 100
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
        "portfolio_values": portfolio_values
    }


def plot_strategy_comparison(ticker, start_date, end_date, starting_cash=10000):
    """
    Compare portfolio equity curves across multiple strategies.
    """
    strategies = ["buy_and_hold", "simple_moving_average", "rsi", "macd"]
    colors = ["blue", "green", "red", "purple"]
    
    df = get_ohlcv(ticker, start_date, end_date)
    dates = pd.to_datetime(df["date"])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for strategy, color in zip(strategies, colors):
        metrics = calculate_metrics(ticker, start_date, end_date, strategy, starting_cash)
        ax.plot(dates, metrics["portfolio_values"], label=strategy, color=color, linewidth=1)
    
    ax.set_xlim(dates.iloc[0], dates.iloc[-1])
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    
    plt.title(f"Strategy Comparison: {ticker} ({start_date} to {end_date})")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig("strategy_comparison.png")
    plt.show()
    
    print("Chart saved as strategy_comparison.png")


if __name__ == "__main__":
    plot_strategy_comparison("NVDA", "2020-01-01", "2023-12-31")
