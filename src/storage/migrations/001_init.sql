CREATE TABLE users (
    telegram_id    INTEGER PRIMARY KEY,
    username       TEXT NOT NULL DEFAULT '',
    role           TEXT NOT NULL DEFAULT 'Member',
    notify_enabled INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One saved search per (user, provider); criteria is provider-specific JSON.
CREATE TABLE searches (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    provider   TEXT NOT NULL,
    criteria   TEXT NOT NULL,
    active     INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, provider)
);

CREATE TABLE offers (
    id         TEXT PRIMARY KEY,          -- "provider:external_id"
    provider   TEXT NOT NULL,
    name       TEXT NOT NULL,
    url        TEXT NOT NULL DEFAULT '',
    address    TEXT NOT NULL DEFAULT '',
    postcode   TEXT NOT NULL DEFAULT '',
    city       TEXT NOT NULL DEFAULT '',
    price      TEXT NOT NULL DEFAULT '',
    size       TEXT NOT NULL DEFAULT '',
    image_url  TEXT NOT NULL DEFAULT '',
    available  INTEGER NOT NULL DEFAULT 1,
    first_seen TEXT NOT NULL,
    last_seen  TEXT NOT NULL
);


-- Notification log. Anti-spam rule: notify (user, offer) only if there is no
-- row with sent_at within the last 24h.
CREATE TABLE deliveries (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    offer_id TEXT NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
    sent_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_deliveries_lookup ON deliveries (user_id, offer_id, sent_at);

CREATE TABLE provider_status (
    provider    TEXT PRIMARY KEY,
    last_run_at TEXT,
    last_ok_at  TEXT,
    last_error  TEXT
);

CREATE TABLE schema_version (version INTEGER NOT NULL);
INSERT INTO schema_version VALUES (1);


