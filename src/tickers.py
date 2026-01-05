import pandas as pd
import requests
from io import StringIO


def get_sp500_tickers():
    """
    Retrieve the current list of S&P 500 constituent tickers from Wikipedia.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    # Explicit user-agent helps avoid request blocking
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    html_content = StringIO(response.text)
    tables = pd.read_html(html_content)
    
    # The first table contains the index constituents
    sp500_table = tables[0]
    tickers = sp500_table["Symbol"].tolist()
    
    return tickers


if __name__ == "__main__":
    tickers = get_sp500_tickers()
    print(f"Found {len(tickers)} tickers")
    print(f"First 10: {tickers[:10]}")
