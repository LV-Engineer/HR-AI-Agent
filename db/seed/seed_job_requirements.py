import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT_ENV = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(ROOT_ENV)

DATABASE_URL = (
    f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@localhost:5432/{os.environ['POSTGRES_DB']}"
)
OLLAMA_URL = os.environ['OLLAMA_URL_LOCAL']
EMBEDDING_MODEL = os.environ['EMBEDDING_MODEL']

engine = create_engine(DATABASE_URL)

VACANCIES = [
    {
        'title': 'Backend Developer (Python)',
        'department': 'Розробка',
        'content': (
            'Шукаємо Backend-розробника з досвідом Python 3+ роки. '
            'Обов’язкові навички: FastAPI або Django, PostgreSQL, Docker. '
            'Буде плюсом: досвід з асинхронним програмуванням, знання SQLAlchemy.'
        ),
    },
    {
        'title': 'HR-менеджер',
        'department': 'HR',
        'content': (
            'Шукаємо HR-менеджера з досвідом підбору персоналу від 2 років. '
            'Обов’язкові навички: проведення інтерв’ю, ведення кадрового документообігу. '
            'Буде плюсом: досвід роботи з ATS-системами.'
        ),
    },
]


def get_embedding(text_input: str) -> list[float]:
    response = httpx.post(
        f'{OLLAMA_URL}/api/embeddings',
        json={'model': EMBEDDING_MODEL, 'prompt': text_input},
        timeout=120.0,
    )
    response.raise_for_status()
    return response.json()['embedding']


def main() -> None:
    with engine.begin() as conn:
        for vacancy in VACANCIES:
            department_id = conn.execute(
                text('SELECT id FROM staff.departments WHERE name = :name'),
                {'name': vacancy['department']},
            ).scalar_one()

            embedding = get_embedding(vacancy['content'])
            vector_literal = '[' + ','.join(str(x) for x in embedding) + ']'
            conn.execute(
                text("""
                    INSERT INTO documents.job_requirements (title, content, department_id, embedding)
                    VALUES (:title, :content, :department_id, (:embedding)::vector)
                """),
                {
                    'title': vacancy['title'],
                    'content': vacancy['content'],
                    'department_id': department_id,
                    'embedding': vector_literal,
                },
            )
    print(f'Seeded {len(VACANCIES)} job requirements.')


if __name__ == '__main__':
    main()