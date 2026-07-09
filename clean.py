import pandas as pd

def clean_stock_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize columns, drop bad rows, cast types for stock price data."""
    df = df.rename(columns={
        "Date": "price_date", "Open": "open_price", "High": "high_price",
        "Low": "low_price", "Close": "close_price", "Volume": "volume",
    })
    # yfinance sometimes returns tz-aware dates -- strip time and tz
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.tz_localize(None).dt.date

    # adj_close isn't always a separate column in newer yfinance versions
    if "Adj Close" in df.columns:
        df = df.rename(columns={"Adj Close": "adj_close"})
    else:
        df["adj_close"] = df["close_price"]

    keep = ["price_date", "open_price", "high_price", "low_price",
            "close_price", "adj_close", "volume"]
    df = df[keep].dropna(subset=["close_price"])
    df = df.drop_duplicates(subset=["price_date"])
    return df


def clean_dividend_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize columns, drop bad rows, cast types for dividend data."""
    if df.empty:
        return df
    df["ex_date"] = pd.to_datetime(df["ex_date"]).dt.tz_localize(None).dt.date
    df = df.dropna(subset=["amount"])
    df = df.drop_duplicates(subset=["ex_date"])
    return df


def clean_macro_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize columns, drop bad rows, cast types for macro indicator data."""
    if df.empty:
        return df
    df["obs_date"] = pd.to_datetime(df["obs_date"]).dt.date
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    return df
