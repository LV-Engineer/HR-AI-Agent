CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS documents;

CREATE TABLE documents.hr_policies (
    id         SERIAL PRIMARY KEY,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    embedding  vector(1024),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE documents.job_requirements (
    id            SERIAL PRIMARY KEY,
    title         TEXT NOT NULL,
    content       TEXT NOT NULL,
    department_id INTEGER REFERENCES staff.departments(id),
    embedding     vector(1024),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE documents.candidate_cv (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_name TEXT,
    content        TEXT,
    file_path      TEXT NOT NULL,
    uploaded_by    UUID REFERENCES auth.users(id),
    embedding      vector(1024),
    uploaded_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);