CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS documents;

CREATE TABLE documents._test (
    id        SERIAL PRIMARY KEY,
    embedding vector(3)
);