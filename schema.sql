CREATE DATABASE IF NOT EXISTS smartcentres_reit
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE smartcentres_reit;

-- ------------------------------------------------------------
-- 1. Companies (SmartCentres + comparator REITs)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    company_id      INT AUTO_INCREMENT PRIMARY KEY,
    ticker          VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(150) NOT NULL,
    sector          VARCHAR(100),
    is_target       BOOLEAN DEFAULT FALSE,   -- TRUE only for SmartCentres
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. Daily stock price history (from yfinance)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_prices (
    price_id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    company_id      INT NOT NULL,
    price_date      DATE NOT NULL,
    open_price      DECIMAL(12,4),
    high_price      DECIMAL(12,4),
    low_price       DECIMAL(12,4),
    close_price     DECIMAL(12,4),
    adj_close       DECIMAL(12,4),
    volume          BIGINT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE KEY uq_company_date (company_id, price_date)
);

-- ------------------------------------------------------------
-- 3. Dividend / distribution history (from yfinance)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dividends (
    dividend_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
    company_id      INT NOT NULL,
    ex_date         DATE NOT NULL,
    amount          DECIMAL(10,6) NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE KEY uq_company_exdate (company_id, ex_date)
);

-- ------------------------------------------------------------
-- 4. Macro indicators (Bank of Canada Valet API)
--    Covers overnight rate target + benchmark bond yields
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS macro_indicators (
    indicator_id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    series_code     VARCHAR(50) NOT NULL,     -- e.g. CBC20210, BD.CDN.10YR.DQ.YLD
    series_label    VARCHAR(150) NOT NULL,    -- human-readable name
    obs_date        DATE NOT NULL,
    value           DECIMAL(10,4),
    UNIQUE KEY uq_series_date (series_code, obs_date)
);
