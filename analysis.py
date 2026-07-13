import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pymongo import MongoClient

from config import DB_CONFIG
from load import get_connection
from mongo_config import MONGO_CONFIG

# ============================================================
# STYLE -- pastel palette, consistent across all charts
# ============================================================

COLORS = {
    "SmartCentres REIT": "#B39DDB",       # lavender (the target -- make it stand out)
    "RioCan REIT": "#F8BBD0",              # peach/pink
    "Choice Properties REIT": "#A5D6A7",   # green
    "First Capital REIT": "#FFE082",       # yellow
}
BG_COLOR = "#FAFAFA"
GRID_COLOR = "#E0E0E0"

plt.rcParams.update({
    "figure.facecolor": BG_COLOR,
    "axes.facecolor": BG_COLOR,
    "axes.edgecolor": "#BDBDBD",
    "axes.grid": True,
    "grid.color": GRID_COLOR,
    "grid.linewidth": 0.6,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
})


# ============================================================
# DATA LOADING FROM MYSQL
# ============================================================

def load_mysql_data():
    """Pull companies, stock_prices, dividends, macro_indicators into pandas."""
    conn = get_connection()

    companies = pd.read_sql("SELECT * FROM companies", conn)
    prices = pd.read_sql(
        """
        SELECT sp.*, c.ticker, c.name
        FROM stock_prices sp
        JOIN companies c ON sp.company_id = c.company_id
        ORDER BY sp.price_date
        """,
        conn,
    )
    dividends = pd.read_sql(
        """
        SELECT d.*, c.ticker, c.name
        FROM dividends d
        JOIN companies c ON d.company_id = c.company_id
        ORDER BY d.ex_date
        """,
        conn,
    )
    macro = pd.read_sql("SELECT * FROM macro_indicators ORDER BY obs_date", conn)

    conn.close()

    prices["price_date"] = pd.to_datetime(prices["price_date"])
    dividends["ex_date"] = pd.to_datetime(dividends["ex_date"])
    macro["obs_date"] = pd.to_datetime(macro["obs_date"])

    return companies, prices, dividends, macro


def load_mongo_summary():
    """Pull a quick count of news articles + SEDAR excerpts per company."""
    client = MongoClient(host=MONGO_CONFIG["host"], port=MONGO_CONFIG["port"])
    db = client[MONGO_CONFIG["database"]]

    news_counts = list(db["news_articles"].aggregate([
        {"$group": {"_id": "$company", "article_count": {"$sum": 1}}}
    ]))
    excerpt_counts = list(db["sedar_excerpts"].aggregate([
        {"$group": {"_id": "$company", "excerpt_count": {"$sum": 1}}}
    ]))

    client.close()
    return news_counts, excerpt_counts


def load_sentiment_summary():
    """
    Pull sentiment label counts per company from news_articles.
    Requires sentiment_analysis.py to have been run first -- if it
    hasn't, sentiment_label won't exist on the documents and this
    returns an empty list (chart is skipped gracefully).
    """
    client = MongoClient(host=MONGO_CONFIG["host"], port=MONGO_CONFIG["port"])
    db = client[MONGO_CONFIG["database"]]

    sentiment_counts = list(db["news_articles"].aggregate([
        {"$match": {"sentiment_label": {"$exists": True}}},
        {"$group": {
            "_id": {"company": "$company", "label": "$sentiment_label"},
            "count": {"$sum": 1},
        }},
    ]))

    client.close()
    return sentiment_counts


# ============================================================
# CHART 1: Normalized price trend
# ============================================================

def chart_normalized_price_trend(prices: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))

    for name, group in prices.groupby("name"):
        group = group.sort_values("price_date")
        base_price = group["close_price"].iloc[0]
        normalized = (group["close_price"] / base_price) * 100
        ax.plot(group["price_date"], normalized, label=name,
                color=COLORS.get(name, "#999999"), linewidth=2)

    ax.set_title("Normalized Price Trend (Rebased to 100)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Indexed Price (Start = 100)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig("chart1_normalized_price_trend.png", dpi=150)
    plt.close(fig)
    print("Saved chart1_normalized_price_trend.png")


# ============================================================
# CHART 2: Dividend yield comparison (most recent full year)
# ============================================================

def chart_dividend_yield_comparison(prices: pd.DataFrame, dividends: pd.DataFrame):
    latest_year = dividends["ex_date"].dt.year.max()

    yields = []
    for name in prices["name"].unique():
        divs_last_year = dividends[
            (dividends["name"] == name) & (dividends["ex_date"].dt.year == latest_year)
        ]["amount"].sum()

        price_group = prices[prices["name"] == name].sort_values("price_date")
        latest_price = price_group["close_price"].iloc[-1]

        yield_pct = (divs_last_year / latest_price) * 100 if latest_price else 0
        yields.append({"name": name, "yield_pct": yield_pct})

    yield_df = pd.DataFrame(yields).sort_values("yield_pct", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bar_colors = [COLORS.get(n, "#999999") for n in yield_df["name"]]
    bars = ax.bar(yield_df["name"], yield_df["yield_pct"], color=bar_colors, edgecolor="white")

    for bar, val in zip(bars, yield_df["yield_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.1, f"{val:.2f}%",
                ha="center", va="bottom", fontsize=10)

    ax.set_title(f"Trailing Dividend Yield Comparison ({latest_year})")
    ax.set_ylabel("Yield (%)")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    fig.tight_layout()
    fig.savefig("chart2_dividend_yield_comparison.png", dpi=150)
    plt.close(fig)
    print("Saved chart2_dividend_yield_comparison.png")

    return yield_df


# ============================================================
# CHART 3: SmartCentres price vs. overnight rate (dual axis)
# ============================================================

def chart_rate_vs_price(prices: pd.DataFrame, macro: pd.DataFrame):
    smartcentres = prices[prices["name"] == "SmartCentres REIT"].sort_values("price_date")
    overnight_rate = macro[macro["series_code"] == "CBC20210"].sort_values("obs_date")

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(smartcentres["price_date"], smartcentres["close_price"],
              color=COLORS["SmartCentres REIT"], linewidth=2, label="SmartCentres Price")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("SmartCentres Close Price ($)", color=COLORS["SmartCentres REIT"])
    ax1.tick_params(axis="y", labelcolor=COLORS["SmartCentres REIT"])

    ax2 = ax1.twinx()
    ax2.plot(overnight_rate["obs_date"], overnight_rate["value"],
              color="#EF9A9A", linewidth=2, linestyle="--", label="Overnight Rate Target")
    ax2.set_ylabel("Overnight Rate Target (%)", color="#EF9A9A")
    ax2.tick_params(axis="y", labelcolor="#EF9A9A")
    ax2.grid(False)

    ax1.set_title("SmartCentres Price vs. Bank of Canada Overnight Rate")
    fig.tight_layout()
    fig.savefig("chart3_rate_vs_price.png", dpi=150)
    plt.close(fig)
    print("Saved chart3_rate_vs_price.png")


# ============================================================
# CHART 4: Rolling volatility comparison (30-day annualized)
# ============================================================

def chart_volatility_comparison(prices: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(10, 6))

    for name, group in prices.groupby("name"):
        group = group.sort_values("price_date").copy()
        group["daily_return"] = group["close_price"].pct_change()
        group["rolling_vol"] = group["daily_return"].rolling(30).std() * (252 ** 0.5) * 100
        ax.plot(group["price_date"], group["rolling_vol"], label=name,
                color=COLORS.get(name, "#999999"), linewidth=1.8)

    ax.set_title("30-Day Rolling Annualized Volatility")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized Volatility (%)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig("chart4_volatility_comparison.png", dpi=150)
    plt.close(fig)
    print("Saved chart4_volatility_comparison.png")


# ============================================================
# CORRELATION: rate changes vs. SmartCentres price changes
# ============================================================

def compute_rate_correlation(prices: pd.DataFrame, macro: pd.DataFrame) -> float:
    smartcentres = prices[prices["name"] == "SmartCentres REIT"][["price_date", "close_price"]].copy()
    overnight_rate = macro[macro["series_code"] == "CBC20210"][["obs_date", "value"]].copy()
    overnight_rate = overnight_rate.rename(columns={"obs_date": "price_date", "value": "rate"})

    merged = pd.merge_asof(
        smartcentres.sort_values("price_date"),
        overnight_rate.sort_values("price_date"),
        on="price_date",
        direction="backward",
    )
    merged["price_change"] = merged["close_price"].pct_change()
    merged["rate_change"] = merged["rate"].diff()

    correlation = merged["price_change"].corr(merged["rate_change"])
    return correlation


# ============================================================
# CHART 5: News sentiment comparison (requires sentiment_analysis.py run first)
# ============================================================

def chart_sentiment_comparison(sentiment_counts: list[dict]):
    if not sentiment_counts:
        print("Skipped chart5_sentiment_comparison.png -- run sentiment_analysis.py first")
        return

    df = pd.DataFrame([
        {"company": row["_id"]["company"], "label": row["_id"]["label"], "count": row["count"]}
        for row in sentiment_counts
    ])
    pivot = df.pivot(index="company", columns="label", values="count").fillna(0)
    for col in ["positive", "neutral", "negative"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot[["positive", "neutral", "negative"]]

    sentiment_colors = {"positive": "#A5D6A7", "neutral": "#FFE082", "negative": "#F8BBD0"}

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bottom = pd.Series([0] * len(pivot), index=pivot.index)
    for label in ["positive", "neutral", "negative"]:
        ax.bar(pivot.index, pivot[label], bottom=bottom, label=label,
               color=sentiment_colors[label], edgecolor="white")
        bottom += pivot[label]

    ax.set_title("News Sentiment Mix by Company")
    ax.set_ylabel("Number of Articles")
    plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig("chart5_sentiment_comparison.png", dpi=150)
    plt.close(fig)
    print("Saved chart5_sentiment_comparison.png")


# ============================================================
# MAIN
# ============================================================

def main():
    print("Loading data from MySQL ...")
    companies, prices, dividends, macro = load_mysql_data()
    print(f"  -> {len(companies)} companies, {len(prices)} price rows, "
          f"{len(dividends)} dividend rows, {len(macro)} macro rows")

    print("\nGenerating charts ...")
    chart_normalized_price_trend(prices)
    yield_df = chart_dividend_yield_comparison(prices, dividends)
    chart_rate_vs_price(prices, macro)
    chart_volatility_comparison(prices)

    print("\nComputing rate-sensitivity correlation ...")
    correlation = compute_rate_correlation(prices, macro)
    print(f"  -> Correlation (SmartCentres daily price change vs. overnight rate change): {correlation:.4f}")

    print("\nDividend yield summary:")
    print(yield_df.to_string(index=False))

    print("\nLoading unstructured data summary from MongoDB ...")
    news_counts, excerpt_counts = load_mongo_summary()
    print("  News article counts per company:")
    for row in news_counts:
        print(f"    {row['_id']}: {row['article_count']} articles")
    print("  SEDAR+ excerpt counts per company:")
    for row in excerpt_counts:
        print(f"    {row['_id']}: {row['excerpt_count']} excerpts")

    print("\nGenerating sentiment comparison chart ...")
    sentiment_counts = load_sentiment_summary()
    chart_sentiment_comparison(sentiment_counts)

    print("\nDone. Charts saved as PNG files in the current folder.")


if __name__ == "__main__":
    main()
