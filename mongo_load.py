"""
Loading unstructured documents into MongoDB.
"""

from datetime import datetime, timezone
from pymongo import MongoClient, UpdateOne

from mongo_config import MONGO_CONFIG


def get_client() -> MongoClient:
    return MongoClient(host=MONGO_CONFIG["host"], port=MONGO_CONFIG["port"])


def get_db(client: MongoClient):
    return client[MONGO_CONFIG["database"]]


def load_news_articles(db, articles: list[dict]):
    if not articles:
        return 0

    collection = db["news_articles"]
    operations = []
    for article in articles:
        doc = {**article, "loaded_at": datetime.now(timezone.utc)}
        # Use link as the natural unique key -- same article won't duplicate on re-run
        operations.append(
            UpdateOne({"link": article["link"]}, {"$set": doc}, upsert=True)
        )

    result = collection.bulk_write(operations)
    return result.upserted_count + result.modified_count


def load_sedar_excerpts(db, excerpts: list[dict]):
    if not excerpts:
        return 0

    collection = db["sedar_excerpts"]
    operations = []
    for excerpt in excerpts:
        doc = {**excerpt, "loaded_at": datetime.now(timezone.utc)}
        key = {"company": excerpt["company"], "section": excerpt["section"], "date": excerpt["date"]}
        operations.append(UpdateOne(key, {"$set": doc}, upsert=True))

    result = collection.bulk_write(operations)
    return result.upserted_count + result.modified_count
