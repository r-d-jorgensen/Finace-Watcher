CREATE TABLE IF NOT EXISTS books (
    book_id             INTEGER     PRIMARY KEY,
    book                TEXT        NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id          INTEGER     PRIMARY KEY,
    book_id             INTEGER     NOT NULL,
    account             TEXT        NOT NULL,
    purpose             TEXT        NOT NULL,
    cash_funds          FLOAT       NOT NULL,
    investment_worth    FLOAT       NOT NULL,
    debt_total          FLOAT       NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS records (
    record_id           INTEGER     PRIMARY KEY,
    account_id          INTEGER     NOT NULL,
    asset_id            INTEGER,
    amount              FLOAT       NOT NULL,
    business            TEXT        NOT NULL,
    category            TEXT        NOT NULL,
    quantity            FLOAT,
    change_type         TEXT        NOT NULL,
    note                TEXT,
    transaction_date    DATETIME    NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
    FOREIGN KEY (asset_id) REFERENCES assets (asset_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id            INTEGER     PRIMARY KEY,
    account_id          INTEGER     NOT NULL,
    asset               TEXT        NOT NULL,
    quantity            FLOAT       NOT NULL,
    market_value        FLOAT       NOT NULL,
    note                TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
);
