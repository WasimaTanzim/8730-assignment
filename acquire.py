import pandas as pd
import requests
import yfinance as yf

from config import START_DATE, END_DATE, VALET_BASE_URL


def fetch_stock_data(ticker: str) -> pd.DataFrame:
    """Pull daily OHLCV history for one ticker via yfinance."""
    df = yf.Ticker(ticker).history(start=START_DATE, end=END_DATE, interval="1d")
    df = df.reset_index()
    return df


def fetch_dividends(ticker: str) -> pd.DataFrame:
    """Pull dividend/distribution history for one ticker via yfinance."""
    divs = yf.Ticker(ticker).dividends
    df = divs.reset_index()
    df.columns = ["ex_date", "amount"]
    return df


def fetch_valet_series(series_code: str) -> pd.DataFrame:
    """Pull one Bank of Canada Valet API series as a raw DataFrame."""
    url = f"{VALET_BASE_URL}/{series_code}/json"
    params = {"start_date": START_DATE, "end_date": END_DATE}
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for obs in data.get("observations", []):
        date = obs.get("d")
        val_block = obs.get(series_code, {})
        value = val_block.get("v")
        if date and value is not None:
            rows.append({"obs_date": date, "value": value})

    return pd.DataFrame(rows)


def fetch_fundamentals(ticker: str) -> dict:
    """
    Pull a point-in-time fundamentals snapshot for one ticker via yfinance.
    Returns market cap, dividend yield, trailing P/E, and beta.
    Any field yfinance doesn't have for a given ticker comes back as None.
    """
    info = yf.Ticker(ticker).info or {}
    return {
        "market_cap": info.get("marketCap"),
        "dividend_yield": info.get("dividendYield"),
        "trailing_pe": info.get("trailingPE"),
        "beta": info.get("beta"),
    }
