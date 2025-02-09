CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS records (
    record_id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    business TEXT NOT NULL,
    note TEXT,
    transaction_date DATETIME NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts (account_id) ON DELETE CASCADE
    FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE CASCADE
);