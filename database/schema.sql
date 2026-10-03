CREATE TABLE decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    difficulty TEXT DEFAULT 'medium',
    next_review_date TIMESTAMP,
    FOREIGN KEY (deck_id) REFERENCES decks(id)
);
