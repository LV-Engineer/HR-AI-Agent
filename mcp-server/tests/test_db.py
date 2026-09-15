import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.db import _validate_select_only, get_schema_info, run_query

pytestmark = pytest.mark.usefixtures('_patch_engine')

class TestValidateSelectOnly:
    def test_accepts_plain_select(self) -> None:
        assert _validate_select_only('SELECT 1') == 'SELECT 1'

    def test_strips_trailing_semicolon(self) -> None:
        assert _validate_select_only('SELECT 1;') == 'SELECT 1'

    def test_case_insensitive(self) -> None:
        assert _validate_select_only('select 1') == 'select 1'

    @pytest.mark.parametrize('sql', [
        "INSERT INTO staff.departments (name) VALUES ('x')",
        "UPDATE staff.departments SET name = 'x'",
        'DELETE FROM staff.departments',
        'DROP TABLE staff.departments',
    ])
    def test_rejects_non_select(self, sql: str) -> None:
        with pytest.raises(ValueError, match='Only SELECT statements'):
            _validate_select_only(sql)

    def test_rejects_multiple_statements(self) -> None:
        with pytest.raises(ValueError, match='single SQL statement'):
            _validate_select_only('SELECT 1; DROP TABLE staff.departments')

class TestGetSchemaInfo:
    def test_returns_allowed_schemas_only(self) -> None:
        schema = get_schema_info()
        assert set(schema.keys()) <= {'staff', 'documents'}

    def test_includes_known_staff_table(self) -> None:
        schema = get_schema_info()
        columns = {col['name'] for col in schema['staff']['employees']}
        assert {'id', 'last_name', 'first_name', 'status_id'} <= columns

class TestRunQuery:
    def test_returns_seeded_rows(self, admin_engine: Engine) -> None:
        with admin_engine.begin() as conn:
            conn.execute(text("INSERT INTO staff.departments (name) VALUES ('Test Dept Alpha')"))

        rows = run_query("SELECT name FROM staff.departments WHERE name = 'Test Dept Alpha'")
        assert rows == [{'name': 'Test Dept Alpha'}]

    def test_rejects_write_query(self) -> None:
        with pytest.raises(ValueError):
            run_query('DELETE FROM staff.departments')

    def test_readonly_role_blocked_at_db_level(self, readonly_engine: Engine) -> None:
        with pytest.raises(Exception):
            with readonly_engine.begin() as conn:
                conn.execute(text("INSERT INTO staff.departments (name) VALUES ('Should Fail')"))