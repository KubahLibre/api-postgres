CREATE TABLE kategorien (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE themen (
    id           SERIAL PRIMARY KEY,
    titel        TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'offen',
    kategorie_id INTEGER NOT NULL REFERENCES kategorien(id),
    notiz        TEXT
);

CREATE TABLE themen_status (
    status TEXT PRIMARY KEY
);

INSERT INTO themen_status (status) VALUES
    ('offen'), ('angefangen'), ('erledigt');

ALTER TABLE themen
    ADD CONSTRAINT themen_status_fkey
    FOREIGN KEY (status) REFERENCES themen_status(status);