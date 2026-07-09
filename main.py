from config import COMPANIES, MACRO_SERIES
from acquire import fetch_stock_data, fetch_dividends, fetch_valet_series, fetch_fundamentals
from clean import clean_stock_df, clean_dividend_df, clean_macro_df
from load import (
    get_connection,
    upsert_company,
    load_stock_prices,
    load_dividends,
    load_macro_indicators,
    load_fundamentals,
)
from mysql.connector import Error as MySQLError


def main():
    try:
        conn = get_connection()
    except MySQLError as e:
        print(f"Could not connect to MySQL: {e}")
        print("Check DB_CONFIG in config.py, and that you ran schema.sql first.")
        return

    cursor = conn.cursor()

    # --- Companies + stock prices + dividends + fundamentals ---
    for company in COMPANIES:
        ticker = company["ticker"]
        print(f"Fetching stock data for {ticker} ...")
        company_id = upsert_company(cursor, company)

        raw_prices = fetch_stock_data(ticker)
        clean_prices = clean_stock_df(raw_prices)
        load_stock_prices(cursor, company_id, clean_prices)
        print(f"  -> loaded {len(clean_prices)} price rows")

        raw_divs = fetch_dividends(ticker)
        clean_divs = clean_dividend_df(raw_divs)
        load_dividends(cursor, company_id, clean_divs)
        print(f"  -> loaded {len(clean_divs)} dividend rows")

        fundamentals = fetch_fundamentals(ticker)
        load_fundamentals(cursor, company_id, fundamentals)
        print(f"  -> loaded fundamentals snapshot "
              f"(market cap: {fundamentals.get('market_cap')}, "
              f"div yield: {fundamentals.get('dividend_yield')}, "
              f"P/E: {fundamentals.get('trailing_pe')}, "
              f"beta: {fundamentals.get('beta')})")

    # --- Macro indicators ---
    for series in MACRO_SERIES:
        print(f"Fetching Bank of Canada series {series['code']} ...")
        raw_macro = fetch_valet_series(series["code"])
        clean_macro = clean_macro_df(raw_macro)
        load_macro_indicators(cursor, series["code"], series["label"], clean_macro)
        print(f"  -> loaded {len(clean_macro)} rows")

    conn.commit()
    cursor.close()
    conn.close()
    print("\nDone. All data acquired, cleaned, and loaded into MySQL.")


if __name__ == "__main__":
    main()
