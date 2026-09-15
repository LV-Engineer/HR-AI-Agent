from sqlalchemy import text

from app.core.db import engine


def match_candidate(cv_id: str, job_requirement_id: int) -> dict:
    sql = text("""
        SELECT
            cv.candidate_name,
            cv.content AS cv_content,
            jr.title AS vacancy_title,
            jr.content AS vacancy_content,
            cv.embedding <-> jr.embedding AS distance
        FROM documents.candidate_cv cv, documents.job_requirements jr
        WHERE cv.id = (:cv_id)::uuid AND jr.id = :job_requirement_id
    """)
    with engine.connect() as conn:
        row = conn.execute(sql, {'cv_id': cv_id, 'job_requirement_id': job_requirement_id}).mappings().one_or_none()

    if row is None:
        raise ValueError('CV or job requirement not found')

    return dict(row)