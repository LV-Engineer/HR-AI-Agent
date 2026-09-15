import re

from sqlalchemy import create_engine, text

from app.core.config import settings

engine = create_engine(settings.database_url)

ALLOWED_SCHEMAS = ('staff', 'documents')
MAX_ROWS = 200


def get_schema_info() -> dict:
    query = text("""
        SELECT table_schema, table_name, column_name,
               CASE WHEN data_type = 'USER-DEFINED' THEN udt_name ELSE data_type END AS type,
               is_nullable
        FROM information_schema.columns
        WHERE table_schema = ANY(:schemas)
        ORDER BY table_schema, table_name, ordinal_position
    """)
    result: dict = {}
    with engine.connect() as conn:
        rows = conn.execute(query, {'schemas': list(ALLOWED_SCHEMAS)})
        for schema, table, column, col_type, is_nullable in rows:
            result.setdefault(schema, {}).setdefault(table, []).append({
                'name': column,
                'type': col_type,
                'nullable': is_nullable == 'YES',
            })
    return result


def _validate_select_only(sql: str) -> str:
    stripped = sql.strip().rstrip(';')
    if ';' in stripped:
        raise ValueError('Only a single SQL statement is allowed.')
    if not re.match(r'^\s*SELECT\b', stripped, re.IGNORECASE):
        raise ValueError('Only SELECT statements are allowed.')
    return stripped


def run_query(sql: str) -> list[dict]:
    validated = _validate_select_only(sql)
    wrapped = f'SELECT * FROM ({validated}) AS subquery LIMIT {MAX_ROWS}'
    with engine.connect() as conn:
        rows = conn.execute(text(wrapped)).mappings().all()
    return [dict(row) for row in rows]
