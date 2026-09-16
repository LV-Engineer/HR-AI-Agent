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

POLICIES = [
    {
        'title': 'Політика відпусток',
        'content': (
            'Кожен співробітник має право на щорічну оплачувану відпустку тривалістю 24 календарні дні. '
            'Заявку на відпустку потрібно подати не пізніше ніж за два тижні до бажаної дати початку. '
            'Невикористані дні відпустки можуть бути перенесені на наступний рік у кількості не більше 10 днів.'
        ),
    },
    {
        'title': 'Політика лікарняних',
        'content': (
            'У разі хвороби співробітник зобов’язаний повідомити свого керівника протягом першого дня відсутності. '
            'Лікарняний лист надається протягом трьох робочих днів після одужання. '
            'Оплата лікарняного здійснюється згідно з чинним законодавством України.'
        ),
    },
    {
        'title': 'Політика віддаленої роботи',
        'content': (
            'Співробітники можуть працювати віддалено за погодженням з безпосереднім керівником. '
            'Під час віддаленої роботи обов’язкова присутність в робочому чаті з 9:00 до 18:00. '
            'Компанія не компенсує витрати на інтернет чи обладнання для віддаленої роботи.'
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
        for policy in POLICIES:
            embedding = get_embedding(policy['content'])
            vector_literal = '[' + ','.join(str(x) for x in embedding) + ']'
            conn.execute(
                text("""
                    INSERT INTO documents.hr_policies (title, content, embedding)
                    VALUES (:title, :content, (:embedding)::vector)
                """),
                {'title': policy['title'], 'content': policy['content'], 'embedding': vector_literal},
            )
    print(f'Seeded {len(POLICIES)} HR policies.')


if __name__ == '__main__':
    main()