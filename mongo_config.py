"""
Configuration for the unstructured data pipeline (MongoDB).
Edit MONGO_CONFIG if your MongoDB isn't running on the default local port.
"""

MONGO_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "database": "smartcentres_reit_unstructured",
}

# Companies to search news for (reuses the same set as the structured pipeline)
NEWS_SEARCH_TERMS = [
    {"company": "SmartCentres REIT", "query": "SmartCentres REIT"},
    {"company": "RioCan REIT", "query": "RioCan REIT"},
    {"company": "Choice Properties REIT", "query": "Choice Properties REIT"},
    {"company": "First Capital REIT", "query": "First Capital REIT"},
]

# Max articles to keep per company (Google News RSS returns quite a few)
MAX_ARTICLES_PER_COMPANY = 15
