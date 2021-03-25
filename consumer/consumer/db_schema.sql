CREATE TABLE IF NOT EXISTS websites (
    id SERIAL PRIMARY KEY,
    url VARCHAR(2048) NOT NULL,
    regexp VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS website_url_idx ON websites (url);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    website_id INTEGER NOT NULL,
    error_code INTEGER NOT NULL,
    response_time REAL NOT NULL,
    matched_text VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (website_id) REFERENCES websites (id)
);
