import ssl
import certifi
import feedparser
from urllib.parse import quote
from urllib.request import Request, urlopen

from mongo_config import NEWS_SEARCH_TERMS, MAX_ARTICLES_PER_COMPANY

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-CA&gl=CA&ceid=CA:en"

# Google will silently reject requests that look like a bare script --
# a normal browser User-Agent avoids that.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
}

# macOS Python often lacks access to the system's trusted CA list --
# using certifi's bundle explicitly avoids CERTIFICATE_VERIFY_FAILED errors.
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def fetch_news_for_company(company: str, query: str) -> list[dict]:
    """Fetch recent news articles for one company via Google News RSS."""
    url = GOOGLE_NEWS_RSS_URL.format(query=quote(query))

    try:
        request = Request(url, headers=HEADERS)
        with urlopen(request, timeout=15, context=SSL_CONTEXT) as response:
            raw_feed = response.read()
    except Exception as e:
        print(f"  ! Could not fetch news for {company}: {e}")
        return []

    feed = feedparser.parse(raw_feed)

    if feed.bozo and not feed.entries:
        print(f"  ! Feed parse issue for {company}: {feed.bozo_exception}")
        return []

    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_COMPANY]:
        articles.append({
            "company": company,
            "title": entry.get("title"),
            "link": entry.get("link"),
            "published": entry.get("published"),
            "source": entry.get("source", {}).get("title") if entry.get("source") else None,
            "summary": entry.get("summary"),
        })
    return articles

def fetch_all_news() -> list[dict]:
    """Fetch news for every company defined in NEWS_SEARCH_TERMS."""
    all_articles = []
    for term in NEWS_SEARCH_TERMS:
        articles = fetch_news_for_company(term["company"], term["query"])
        all_articles.extend(articles)
    return all_articles
