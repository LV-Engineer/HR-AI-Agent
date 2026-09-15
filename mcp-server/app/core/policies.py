from sqlalchemy import text

from app.core.db import engine
from app.core.embeddings import get_embedding

def search_hr_policies(query: str, limit: int = 3) -> list[dict]:
    query_embedding = get_embedding(query)
    vector_literal = '[' + ','.join(str(x) for x in query_embedding) + ']'
    sql = text("""
        SELECT title, content, embedding <-> (:embedding)::vector AS distance
        FROM documents.hr_policies
        ORDER BY embedding <-> (:embedding)::vector
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {'embedding': vector_literal, 'limit': limit}).mappings().all()
    return [dict(row) for row in rows]