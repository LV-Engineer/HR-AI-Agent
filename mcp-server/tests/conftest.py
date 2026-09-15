import os
from pathlib import Path
from typing import Generator

os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://placeholder:placeholder@localhost:5432/placeholder')
os.environ.setdefault('OLLAMA_URL', 'http://placeholder:11434')

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from testcontainers.postgres import PostgresContainer

INIT_DIR = Path(__file__).resolve().parents[2] / 'db' / 'init'

READONLY_USER = 'mcp_readonly_test'
READONLY_PASSWORD = 'test_readonly_pw'

DIM = 1024

def _basis_vector(index: int) -> list[float]:
    vec = [0.0] * DIM
    vec[index] = 1.0
    return vec

def _vector_literal(vec: list[float]) -> str:
    return '[' + ','.join(str(x) for x in vec) + ']'

def _connection_url(container: PostgresContainer, username: str, password: str) -> str:
    return (
        f'postgresql+psycopg://{username}:{password}'
        f'@{container.get_container_host_ip()}:{container.get_exposed_port(5432)}/{container.dbname}'
    )

def _generate_engine(url: str) -> Generator[Engine, None, None]:
    engine = create_engine(url)
    yield engine
    engine.dispose()

@pytest.fixture(scope='session')
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer('pgvector/pgvector:pg16', username='test', password='test', dbname='test') as container:
        admin_url = _connection_url(container, container.username, container.password)
        admin_engine = create_engine(admin_url)
        for sql_file in sorted(INIT_DIR.glob('*.sql')):
            with admin_engine.begin() as conn:
                conn.execute(text(sql_file.read_text()))
        with admin_engine.begin() as conn:
            conn.execute(text(f"""
                CREATE ROLE {READONLY_USER} WITH LOGIN PASSWORD '{READONLY_PASSWORD}';
                GRANT USAGE ON SCHEMA staff, documents TO {READONLY_USER};
                GRANT SELECT ON ALL TABLES IN SCHEMA staff, documents TO {READONLY_USER};
                ALTER DEFAULT PRIVILEGES IN SCHEMA staff, documents GRANT SELECT ON TABLES TO {READONLY_USER};
            """))
        admin_engine.dispose()
        yield container

@pytest.fixture(scope='session')
def admin_url(postgres_container: PostgresContainer) -> str:
    return _connection_url(postgres_container, postgres_container.username, postgres_container.password)

@pytest.fixture(scope='session')
def readonly_url(postgres_container: PostgresContainer) -> str:
    return _connection_url(postgres_container, READONLY_USER, READONLY_PASSWORD)

@pytest.fixture(scope='session')
def admin_engine(admin_url: str) -> Generator[Engine, None, None]:
    yield from _generate_engine(admin_url)

@pytest.fixture(scope='session')
def readonly_engine(readonly_url: str) -> Generator[Engine, None, None]:
    yield from _generate_engine(readonly_url)

@pytest.fixture
def _patch_engine(readonly_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import db as db_module
    from app.core import matching as matching_module
    from app.core import policies as policies_module

    monkeypatch.setattr(db_module, 'engine', readonly_engine)
    monkeypatch.setattr(matching_module, 'engine', readonly_engine)
    monkeypatch.setattr(policies_module, 'engine', readonly_engine)