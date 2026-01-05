import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.database import get_ohlcv, get_existing_tickers, init_database
from src.backtester import calculate_metrics

# Page configuration
st.set_page_config(
    page_title="Backtesting Engine",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📈 Algorithmic Trading Backtesting Engine")
st.write("Compare trading strategies on S&P 500 stocks using 10 years of historical data.")

from src.downloader import download_all_tickers

# Demo tickers for Streamlit Cloud
DEMO_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", 
                "META", "TSLA", "JPM", "V", "WMT"]

# Initialize database
init_database()

# Check if we have data
existing_tickers = get_existing_tickers()

if len(existing_tickers) == 0:
    st.warning("No data found. Downloading demo data (10 stocks, 5 years)...")
    with st.spinner("This may take a few minutes on first run..."):
        download_all_tickers(DEMO_TICKERS, years=5)
    existing_tickers = get_existing_tickers()
    st.success(f"Downloaded data for {len(existing_tickers)} stocks!")
    st.rerun()  # Refresh the page

# Sidebar for inputs
st.sidebar.header("Settings")

ticker = st.sidebar.selectbox(
    "Select Stock",
    options=existing_tickers,
    index=existing_tickers.index("AAPL") if "AAPL" in existing_tickers else 0
)

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=pd.to_datetime("2020-01-01")
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=pd.to_datetime("2023-12-31")
    )

starting_cash = st.sidebar.number_input(
    "Starting Cash ($)",
    min_value=1000,
    max_value=1000000,
    value=10000,
    step=1000
)

# Run backtest button
if st.sidebar.button("Run Backtest", type="primary"):
    
    # Validate dates
    if start_date >= end_date:
        st.error("End date must be after start date.")
        st.stop()
    
    # Show loading spinner
    with st.spinner("Running backtest..."):
        
        strategies = ["buy_and_hold", "simple_moving_average", "rsi", "macd"]
        strategy_names = ["Buy & Hold", "Simple Moving Average", "RSI", "MACD"]
        colors = ["blue", "green", "red", "purple"]
        
        results = []
        all_metrics = []
        
        for strategy, name in zip(strategies, strategy_names):
            m = calculate_metrics(
                ticker,
                str(start_date),
                str(end_date),
                strategy,
                starting_cash
            )
            if m:
                all_metrics.append(m)
                results.append({
                    "Strategy": name,
                    "Total Return": f"{m['total_return']}%",
                    "Annual Return": f"{m['annual_return']}%",
                    "Max Drawdown": f"{m['max_drawdown']}%",
                    "Trades": m['num_trades'],
                    "Win Rate": f"{m['win_rate']}%",
                    "End Value": f"${m['portfolio_values'][-1]:,.2f}"
                })
    
    # Display results
    st.header(f"Results: {ticker}")
    
    # Calculate best ending value
    best_end_value = max(m['portfolio_values'][-1] for m in all_metrics)
    
    st.write(f"Period: {start_date} to {end_date} | Starting Capital: \${starting_cash:,} | Best End Value: \${best_end_value:,.2f}")
    
    # Results table
    st.subheader("📊 Performance Comparison")
    results_df = pd.DataFrame(results)
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    
    # Key metrics cards
    st.subheader("🏆 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    # Best return
    best_return_idx = max(range(len(all_metrics)), key=lambda i: all_metrics[i]['total_return'])
    with col1:
        st.metric(
            label="Best Return",
            value=f"{all_metrics[best_return_idx]['total_return']}%",
            delta=strategy_names[best_return_idx]
        )
    
    # Lowest drawdown
    lowest_dd_idx = max(range(len(all_metrics)), key=lambda i: all_metrics[i]['max_drawdown'])
    with col2:
        st.metric(
            label="Lowest Drawdown",
            value=f"{all_metrics[lowest_dd_idx]['max_drawdown']}%",
            delta=strategy_names[lowest_dd_idx]
        )
    
    # Best win rate
    best_wr_idx = max(range(len(all_metrics)), key=lambda i: all_metrics[i]['win_rate'])
    with col3:
        st.metric(
            label="Best Win Rate",
            value=f"{all_metrics[best_wr_idx]['win_rate']}%",
            delta=strategy_names[best_wr_idx]
        )
    
    # Portfolio value chart
    st.subheader("📈 Portfolio Value Over Time")
    
    # Get dates for x-axis
    df = get_ohlcv(ticker, str(start_date), str(end_date))
    dates = pd.to_datetime(df["date"])
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for m, name, color in zip(all_metrics, strategy_names, colors):
        ax.plot(dates, m["portfolio_values"], label=name, color=color, linewidth=1.5)
    
    ax.set_xlim(dates.iloc[0], dates.iloc[-1])
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=45)
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Strategy explanations
    with st.expander("📚 Strategy Explanations"):
        st.markdown("""
        **Buy & Hold**: Buy on day one, hold until the end. The baseline strategy.
        
        **Simple Moving Average (SMA)**: 
        - Buy when price crosses above 20-day average
        - Sell when price crosses below 20-day average
        
        **RSI (Relative Strength Index)**:
        - Buy when RSI drops below 30 (oversold)
        - Sell when RSI rises above 70 (overbought)
        
        **MACD (Moving Average Convergence Divergence)**:
        - Buy when MACD line crosses above signal line
        - Sell when MACD line crosses below signal line
        """)

else:
    # Show instructions when app first loads
    st.info("👈 Configure your backtest settings in the sidebar and click 'Run Backtest'")
    
    st.markdown("""
    ### How to Use
    1. Select a stock from the dropdown
    2. Choose your date range
    3. Set your starting capital
    4. Click **Run Backtest**
    
    ### About This Project
    This backtesting engine was built to compare different trading strategies 
    on historical S&P 500 stock data. It downloads 10 years of data and tests
    four common trading strategies.
    
    **Built with:** Python, pandas, NumPy, SQLite, matplotlib, Streamlit
    
    [View Source Code on GitHub](https://github.com/JojoKrueger/Algorithmic-Trading-Backtesting-Engine)
    """)