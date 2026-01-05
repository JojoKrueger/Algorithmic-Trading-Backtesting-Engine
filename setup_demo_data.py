from src.database import init_database
from src.downloader import download_all_tickers

# Just 10 popular stocks for the demo
demo_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", 
                "META", "TSLA", "JPM", "V", "WMT"]

init_database()
download_all_tickers(demo_tickers, years=5)  # 5 years to keep file smaller