from pymongo import MongoClient

from mongo_config import MONGO_CONFIG

POSITIVE_WORDS = [
    "strong", "growth", "beat", "record", "raised", "increase", "outperform",
    "gain", "rally", "surge", "profit", "upgrade", "expansion", "solid",
    "resilient", "robust", "exceed", "positive",
]

NEGATIVE_WORDS = [
    "miss", "loss", "decline", "weak", "cut", "concern", "risk", "fell",
    "downgrade", "drop", "plunge", "warning", "lawsuit", "delay", "layoff",
    "default", "negative", "struggle",
]


def score_text(text: str) -> tuple[int, str]:
    """Return a (score, label) pair based on keyword counts in the text."""
    text_lower = str(text).lower()
    positive_hits = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_hits = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
    score = positive_hits - negative_hits

    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"

    return score, label


def score_all_articles(db) -> dict:
    """Score every article in news_articles, write the result back, return a summary."""
    collection = db["news_articles"]
    articles = list(collection.find({}))

    summary = {}
    for article in articles:
        combined_text = f"{article.get('title', '')} {article.get('summary', '')}"
        score, label = score_text(combined_text)

        collection.update_one(
            {"_id": article["_id"]},
            {"$set": {"sentiment_score": score, "sentiment_label": label}},
        )

        company = article.get("company", "Unknown")
        summary.setdefault(company, {"positive": 0, "neutral": 0, "negative": 0})
        summary[company][label] += 1

    return summary


def print_summary(summary: dict):
    print("\nSentiment summary by company:")
    print(f"{'Company':<28}{'Positive':>10}{'Neutral':>10}{'Negative':>10}{'Net tone':>12}")
    for company, counts in summary.items():
        total = counts["positive"] + counts["neutral"] + counts["negative"]
        net_tone = (counts["positive"] - counts["negative"]) / total * 100 if total else 0
        print(f"{company:<28}{counts['positive']:>10}{counts['neutral']:>10}"
              f"{counts['negative']:>10}{net_tone:>11.1f}%")


def main():
    client = MongoClient(host=MONGO_CONFIG["host"], port=MONGO_CONFIG["port"])
    db = client[MONGO_CONFIG["database"]]

    print("Scoring news articles ...")
    summary = score_all_articles(db)
    print(f"  -> scored {sum(sum(c.values()) for c in summary.values())} articles")

    print_summary(summary)

    client.close()
    print("\nDone. Sentiment scores written back to news_articles.")


if __name__ == "__main__":
    main()
