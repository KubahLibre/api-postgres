CREATE TABLE kategorien (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE themen_status (
    status TEXT PRIMARY KEY
);

INSERT INTO themen_status (status) VALUES
    ('offen'), ('angefangen'), ('erledigt');

CREATE TABLE themen (
    id           SERIAL PRIMARY KEY,
    titel        TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'offen' REFERENCES themen_status(status),
    kategorie_id INTEGER NOT NULL REFERENCES kategorien(id),
    notiz        TEXT
);
