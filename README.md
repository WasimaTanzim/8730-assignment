# 8730-assignment: SmartCentres REIT Investment Analysis

BSMM-8730 Data Acquisition and Management — Group Project (Group 9)
University of Windsor, Odette School of Business

## Project Overview

An end-to-end data analytics pipeline evaluating **SmartCentres Real Estate
Investment Trust (REIT)** from the perspective of a potential investor. The
project acquires, cleans, and analyzes structured financial data (stock
prices, dividends, macroeconomic indicators) and unstructured data (news
articles, SEDAR+ filing excerpts) to produce an investment recommendation.

**Comparator REITs:** RioCan, Choice Properties, First Capital

## Architecture

- **MySQL** — structured data: stock prices, dividends, macroeconomic
  indicators (interest rates, bond yields)
- **MongoDB** — unstructured data: news articles, SEDAR+ filing excerpts
- **Python** — acquisition, cleaning, loading, and analysis pipeline

## Data Sources

- [yfinance](https://pypi.org/project/yfinance/) — stock prices and
  dividend history
- [Bank of Canada Valet API](https://www.bankofcanada.ca/valet-api-how-to/) —
  overnight rate target and benchmark bond yields
- Google News RSS — recent news coverage per company
- [SEDAR+](https://www.sedarplus.ca/) — regulatory filings (manually
  sourced excerpts, since SEDAR+ has no public API)
- [SmartCentres investor relations](https://smartcentres.com/) — press
  releases and quarterly results

## Repository Structure

```
8730-assignment/
├── README.md
├── .gitignore
├── schema.sql                  # MySQL schema
├── config.py                   # MySQL connection + pipeline config
├── acquire.py                  # yfinance + Bank of Canada data fetching
├── clean.py                    # Data cleaning/validation
├── load.py                     # MySQL loading logic
├── main.py                     # Structured pipeline entry point
├── mongo_config.py             # MongoDB connection + news search config
├── news_acquire.py             # Google News RSS fetching
├── sedar_excerpts.py           # Manually-collected SEDAR+ excerpts
├── mongo_load.py                # MongoDB loading logic
├── main_unstructured.py        # Unstructured pipeline entry point
├── sentiment_analysis.py       # News sentiment scoring
├── analysis.py                  # Charts + correlation + sentiment analysis
└── docs/
    └── recommendation.md        # Final investment recommendation
```

## Environment Setup

### Prerequisites
- Python 3.10+
- MySQL (via Homebrew: `brew install mysql`)
- MongoDB (via Homebrew: `brew tap mongodb/brew && brew install mongodb-community`)

### 1. Install Python dependencies
```bash
python3 -m pip install yfinance mysql-connector-python pymongo feedparser certifi pandas matplotlib requests --break-system-packages
```

### 2. Start the databases
```bash
brew services start mysql
brew services start mongodb-community
```

### 3. Set up the MySQL schema
```bash
mysql -u root -p < schema.sql
```

### 4. Configure credentials
Edit `config.py` and set your MySQL password in `DB_CONFIG`.
Edit `mongo_config.py` if MongoDB isn't running on the default local port.

## How to Run

Run the four pipeline stages in this order:

### 1. Structured data pipeline (MySQL)
```bash
python3 main.py
```
Fetches and loads stock prices, dividends, fundamentals, and
macroeconomic indicators for SmartCentres and the three comparator
REITs.

### 2. Unstructured data pipeline (MongoDB)
```bash
python3 main_unstructured.py
```
Fetches news articles and loads SEDAR+ excerpts.

### 3. Sentiment scoring
```bash
python3 sentiment_analysis.py
```
Scores the news articles already loaded into MongoDB and writes
sentiment labels back onto each document.

### 4. Analysis
```bash
python3 analysis.py
```
Generates 5 comparison charts (normalized price trend, dividend yield,
rate-sensitivity, volatility, news sentiment), computes the
rate-sensitivity correlation, and prints a summary of key findings.

See `docs/recommendation.md` for the final investment recommendation
based on this analysis.

## Use of Large Language Models

This project used an LLM (Claude, by Anthropic) as a coding and research
assistant during development. All submitted content, code, and analysis
have been reviewed and are understood by the team. Prompts used are
included in the submission per course requirements.

## Team

Group 9 — Anushka Pradeep, Xinyun Gu, Wasima Tanzim, Yifan Chen

## Instructor

Professor Ali El-Sharif ([@elsharif-UWindsor](https://github.com/elsharif-UWindsor))
