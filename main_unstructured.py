"""
BSMM-8730 Project: SmartCentres REIT Investment Analysis
Unstructured data pipeline entry point.

Pulls news articles (via Google News RSS) and loads manually-collected
SEDAR+ excerpts into MongoDB.

Run:
    python3 main_unstructured.py
"""

from news_acquire import fetch_all_news
from sedar_excerpts import SEDAR_EXCERPTS
from mongo_load import get_client, get_db, load_news_articles, load_sedar_excerpts


def main():
    try:
        client = get_client()
        client.admin.command("ping")   # fail fast if MongoDB isn't reachable
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        print("Check that MongoDB is running: brew services list")
        return

    db = get_db(client)

    print("Fetching news articles ...")
    articles = fetch_all_news()
    news_count = load_news_articles(db, articles)
    print(f"  -> loaded {news_count} news articles (from {len(articles)} fetched)")

    print("Loading SEDAR+ excerpts ...")
    excerpt_count = load_sedar_excerpts(db, SEDAR_EXCERPTS)
    print(f"  -> loaded {excerpt_count} SEDAR+ excerpts")

    client.close()
    print("\nDone. Unstructured data loaded into MongoDB.")


if __name__ == "__main__":
    main()
