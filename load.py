import pandas as pd
import mysql.connector

from config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def upsert_company(cursor, company: dict) -> int:
    cursor.execute(
        """
        INSERT INTO companies (ticker, name, sector, is_target)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=VALUES(name), sector=VALUES(sector),
                                 is_target=VALUES(is_target)
        """,
        (company["ticker"], company["name"], company["sector"], company["is_target"]),
    )
    cursor.execute("SELECT company_id FROM companies WHERE ticker = %s", (company["ticker"],))
    return cursor.fetchone()[0]


def load_stock_prices(cursor, company_id: int, df: pd.DataFrame):
    rows = [
        (company_id, r.price_date, r.open_price, r.high_price, r.low_price,
         r.close_price, r.adj_close, int(r.volume) if pd.notna(r.volume) else None)
        for r in df.itertuples(index=False)
    ]
    cursor.executemany(
        """
        INSERT INTO stock_prices
            (company_id, price_date, open_price, high_price, low_price, close_price, adj_close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            open_price=VALUES(open_price), high_price=VALUES(high_price),
            low_price=VALUES(low_price), close_price=VALUES(close_price),
            adj_close=VALUES(adj_close), volume=VALUES(volume)
        """,
        rows,
    )


def load_dividends(cursor, company_id: int, df: pd.DataFrame):
    if df.empty:
        return
    rows = [(company_id, r.ex_date, r.amount) for r in df.itertuples(index=False)]
    cursor.executemany(
        """
        INSERT INTO dividends (company_id, ex_date, amount)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE amount=VALUES(amount)
        """,
        rows,
    )


def load_macro_indicators(cursor, series_code: str, series_label: str, df: pd.DataFrame):
    if df.empty:
        return
    rows = [(series_code, series_label, r.obs_date, r.value) for r in df.itertuples(index=False)]
    cursor.executemany(
        """
        INSERT INTO macro_indicators (series_code, series_label, obs_date, value)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE value=VALUES(value)
        """,
        rows,
    )

def load_fundamentals(cursor, company_id: int, fundamentals: dict):
    """
    Insert a fundamentals snapshot keyed by (company_id, snapshot_date).
    Re-running on the same day updates the existing snapshot instead of
    creating a duplicate; running on a new day creates a fresh snapshot,
    so historical fundamentals accumulate over time.
    """
    cursor.execute(
        """
        INSERT INTO fundamentals (company_id, market_cap, dividend_yield, trailing_pe, beta, snapshot_date)
        VALUES (%s, %s, %s, %s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE
            market_cap=VALUES(market_cap), dividend_yield=VALUES(dividend_yield),
            trailing_pe=VALUES(trailing_pe), beta=VALUES(beta)
        """,
        (
            company_id,
            fundamentals.get("market_cap"),
            fundamentals.get("dividend_yield"),
            fundamentals.get("trailing_pe"),
            fundamentals.get("beta"),
        ),
    )
