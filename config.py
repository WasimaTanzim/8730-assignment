DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "newpassword",   # <-- change this
    "database": "smartcentres_reit",
}

# Date range for stock/dividend history and macro data
START_DATE = "2019-01-01"
END_DATE = "2026-07-01"

# Companies: SmartCentres is the target, the rest are comparators
COMPANIES = [
    {"ticker": "SRU-UN.TO", "name": "SmartCentres REIT",      "sector": "Retail REIT", "is_target": True},
    {"ticker": "REI-UN.TO", "name": "RioCan REIT",            "sector": "Retail REIT", "is_target": False},
    {"ticker": "CHP-UN.TO", "name": "Choice Properties REIT", "sector": "Retail REIT", "is_target": False},
    {"ticker": "FCR-UN.TO", "name": "First Capital REIT",     "sector": "Retail REIT", "is_target": False},
]

# Bank of Canada Valet series to pull
MACRO_SERIES = [
    {"code": "CBC20210",           "label": "Overnight Rate Target"},
    {"code": "BD.CDN.10YR.DQ.YLD", "label": "10-Year Benchmark Bond Yield"},
]

VALET_BASE_URL = "https://www.bankofcanada.ca/valet/observations"
