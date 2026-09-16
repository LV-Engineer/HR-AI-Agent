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

CANDIDATES = [
    {
        'candidate_name': 'Іван Коваленко',
        'file_path': '/storage/cv/ivan_kovalenko.pdf',
        'content': (
            'Python-розробник з 4-річним досвідом. Працював з FastAPI, PostgreSQL, Docker. '
            'Маю досвід асинхронного програмування (asyncio), знайомий з SQLAlchemy. '
            'Останній проєкт — мікросервісна архітектура на FastAPI з інтеграцією Redis.'
        ),
    },
    {
        'candidate_name': 'Олена Ткаченко',
        'file_path': '/storage/cv/olena_tkachenko.pdf',
        'content': (
            'Маркетолог з 3-річним досвідом у SMM та контент-маркетингу. '
            'Не маю досвіду програмування чи технічних навичок.'
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
        for candidate in CANDIDATES:
            embedding = get_embedding(candidate['content'])
            vector_literal = '[' + ','.join(str(x) for x in embedding) + ']'
            conn.execute(
                text("""
                    INSERT INTO documents.candidate_cv (candidate_name, content, file_path, embedding)
                    VALUES (:candidate_name, :content, :file_path, (:embedding)::vector)
                """),
                {
                    'candidate_name': candidate['candidate_name'],
                    'content': candidate['content'],
                    'file_path': candidate['file_path'],
                    'embedding': vector_literal,
                },
            )
    print(f'Seeded {len(CANDIDATES)} candidate CVs.')


if __name__ == '__main__':
    main()