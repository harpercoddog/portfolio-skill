CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    market TEXT NOT NULL,
    base_currency TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    market TEXT NOT NULL,
    name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    currency TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_price NUMERIC,
    last_price_date TEXT,
    last_price_source TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, market)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    account_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    quantity NUMERIC NOT NULL DEFAULT 0,
    unit_price NUMERIC NOT NULL DEFAULT 0,
    gross_amount NUMERIC NOT NULL DEFAULT 0,
    fee NUMERIC NOT NULL DEFAULT 0,
    currency TEXT NOT NULL,
    note TEXT,
    raw_text TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE RESTRICT,
    FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_transactions_account_asset_date
ON transactions(account_id, asset_id, trade_date, id);

CREATE INDEX IF NOT EXISTS idx_transactions_asset_date
ON transactions(asset_id, trade_date, id);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    price_date TEXT NOT NULL,
    close_price NUMERIC NOT NULL,
    prev_close_price NUMERIC,
    currency TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    UNIQUE(asset_id, price_date, source)
);

CREATE INDEX IF NOT EXISTS idx_price_history_asset_date
ON price_history(asset_id, price_date DESC, id DESC);

