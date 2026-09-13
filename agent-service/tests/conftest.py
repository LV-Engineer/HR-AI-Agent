from typing import Generator
import os
from pathlib import Path

os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://placeholder:placeholder@localhost:5432/placeholder')
os.environ.setdefault('REDIS_URL', 'memory://')
os.environ.setdefault('COMPANY_EMAIL_DOMAIN', 'hirelume.dev')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('JWT_ALGORITHM', 'HS256')
os.environ.setdefault('ACCESS_TOKEN_EXPIRE_MINUTES', '30')
os.environ.setdefault('REFRESH_TOKEN_EXPIRE_DAYS', '30')

TEST_EMAIL = 'test.user@hirelume.dev'
TEST_PASSWORD = 'password123'

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

from app.core.db import get_db
from app.main import app
from app.core.rate_limit import limiter

INIT_DIR = Path(__file__).resolve().parents[2] / 'db' / 'init'

@pytest.fixture(scope='session')
def postgres_url() -> Generator[str, None, None]:
    with PostgresContainer('pgvector/pgvector:pg16', username='test', password='test', dbname='test') as container:
        url = (
            f'postgresql+psycopg://{container.username}:{container.password}'
            f'@{container.get_container_host_ip()}:{container.get_exposed_port(5432)}/{container.dbname}'
        )
        engine = create_engine(url)
        for sql_file in sorted(INIT_DIR.glob('*.sql')):
            with engine.begin() as conn:
                conn.execute(text(sql_file.read_text()))
        engine.dispose()
        yield url

@pytest.fixture(scope='session')
def engine(postgres_url: str):
    eng = create_engine(postgres_url)
    yield eng
    eng.dispose()

@pytest.fixture
def db_session(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode='create_savepoint')
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    limiter.reset()
    yield

@pytest.fixture
def test_user(db_session: Session) -> tuple[str, str]:
    db_session.execute(
        text('SELECT auth.create_user(:email, :password)'),
        {'email': TEST_EMAIL, 'password': TEST_PASSWORD},
    )
    db_session.commit()
    return TEST_EMAIL, TEST_PASSWORD