import os
import random
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text

ROOT_ENV = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(ROOT_ENV)

DATABASE_URL = (
    f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@localhost:5432/{os.environ['POSTGRES_DB']}"
)

engine = create_engine(DATABASE_URL)
fake = Faker('uk_UA')

EMPLOYEE_COUNT = 90

DEPARTMENTS = [
    'Розробка', 'Продажі', 'Маркетинг', 'Бухгалтерія',
    'HR', 'Підтримка клієнтів', 'Юридичний відділ', 'Адміністрація',
]

POSITIONS = [
    'Розробник', 'Тімлід', 'Менеджер з продажів', 'Бухгалтер',
    'HR-менеджер', 'Спеціаліст підтримки', 'Юрист', 'Керівник відділу',
    'Маркетолог', 'Аналітик', 'Офіс-менеджер',
]

EMPLOYEE_STATUSES = ['active', 'terminated']
EMPLOYMENT_CHANGE_REASONS = ['hire', 'promotion', 'transfer']
VACATION_TYPES = ['vacation', 'sick_leave']
TERMINATION_REASONS = ['voluntary', 'involuntary', 'layoff']


def seed_lookup(conn, table: str, codes: list[str]) -> dict[str, int]:
    ids = {}
    for code in codes:
        row = conn.execute(
            text(f'INSERT INTO staff.{table} (code) VALUES (:code) RETURNING id'),
            {'code': code},
        ).one()
        ids[code] = row.id
    return ids


def seed_departments(conn) -> dict[str, int]:
    ids = {}
    for name in DEPARTMENTS:
        row = conn.execute(
            text('INSERT INTO staff.departments (name) VALUES (:name) RETURNING id'),
            {'name': name},
        ).one()
        ids[name] = row.id
    return ids


def seed_positions(conn) -> dict[str, int]:
    ids = {}
    for title in POSITIONS:
        row = conn.execute(
            text('INSERT INTO staff.positions (title) VALUES (:title) RETURNING id'),
            {'title': title},
        ).one()
        ids[title] = row.id
    return ids


def random_hire_date() -> date:
    days_back = random.randint(30, 5 * 365)
    return date.today() - timedelta(days=days_back)


def seed_employees(conn, status_ids: dict[str, int]) -> list[dict]:
    employees = []
    for _ in range(EMPLOYEE_COUNT):
        is_terminated = random.random() < 0.1
        row = conn.execute(
            text("""
                INSERT INTO staff.employees (last_name, first_name, middle_name, hired_at, status_id)
                VALUES (:last_name, :first_name, :middle_name, :hired_at, :status_id)
                RETURNING id
            """),
            {
                'last_name': fake.last_name(),
                'first_name': fake.first_name(),
                'middle_name': fake.middle_name() if random.random() < 0.8 else None,
                'hired_at': random_hire_date(),
                'status_id': status_ids['terminated' if is_terminated else 'active'],
            },
        ).one()
        employees.append({'id': row.id, 'terminated': is_terminated})

    # призначити ~10% менеджерами серед активних співробітників
    active_employees = [emp for emp in employees if not emp['terminated']]
    manager_pool = random.sample(active_employees, max(1, len(active_employees) // 10))
    for emp in employees:
        if emp in manager_pool:
            continue
        manager = random.choice(manager_pool)
        conn.execute(
            text('UPDATE staff.employees SET manager_id = :manager_id WHERE id = :id'),
            {'manager_id': manager['id'], 'id': emp['id']},
        )
    return employees


def seed_employment_changes(conn, employees, dept_ids, pos_ids, reason_ids):
    dept_values = list(dept_ids.values())
    pos_values = list(pos_ids.values())
    for emp in employees:
        hired_at = conn.execute(
            text('SELECT hired_at FROM staff.employees WHERE id = :id'), {'id': emp['id']}
        ).scalar_one()
        conn.execute(
            text("""
                INSERT INTO staff.employment_changes (employee_id, department_id, position_id, effective_from, reason_id)
                VALUES (:employee_id, :department_id, :position_id, :effective_from, :reason_id)
            """),
            {
                'employee_id': emp['id'],
                'department_id': random.choice(dept_values),
                'position_id': random.choice(pos_values),
                'effective_from': hired_at,
                'reason_id': reason_ids['hire'],
            },
        )
        if random.random() < 0.2:
            conn.execute(
                text("""
                    INSERT INTO staff.employment_changes (employee_id, department_id, position_id, effective_from, reason_id)
                    VALUES (:employee_id, :department_id, :position_id, :effective_from, :reason_id)
                """),
                {
                    'employee_id': emp['id'],
                    'department_id': random.choice(dept_values),
                    'position_id': random.choice(pos_values),
                    'effective_from': hired_at + timedelta(days=random.randint(180, 900)),
                    'reason_id': reason_ids[random.choice(['promotion', 'transfer'])],
                },
            )


def seed_salaries(conn, employees):
    for emp in employees:
        hired_at = conn.execute(
            text('SELECT hired_at FROM staff.employees WHERE id = :id'), {'id': emp['id']}
        ).scalar_one()
        amount = random.randint(20000, 60000)
        conn.execute(
            text("""
                INSERT INTO staff.salaries (employee_id, amount, effective_from)
                VALUES (:employee_id, :amount, :effective_from)
            """),
            {'employee_id': emp['id'], 'amount': amount, 'effective_from': hired_at},
        )
        if random.random() < 0.4:
            raise_amount = amount + random.randint(2000, 10000)
            conn.execute(
                text("""
                    INSERT INTO staff.salaries (employee_id, amount, effective_from)
                    VALUES (:employee_id, :amount, :effective_from)
                """),
                {
                    'employee_id': emp['id'],
                    'amount': raise_amount,
                    'effective_from': hired_at + timedelta(days=random.randint(180, 900)),
                },
            )


def seed_vacations(conn, employees, type_ids):
    for emp in employees:
        for _ in range(random.randint(0, 3)):
            start = date.today() - timedelta(days=random.randint(0, 700))
            end = start + timedelta(days=random.randint(1, 14))
            conn.execute(
                text("""
                    INSERT INTO staff.vacations (employee_id, type_id, start_date, end_date)
                    VALUES (:employee_id, :type_id, :start_date, :end_date)
                """),
                {
                    'employee_id': emp['id'],
                    'type_id': type_ids[random.choice(VACATION_TYPES)],
                    'start_date': start,
                    'end_date': end,
                },
            )


def seed_terminations(conn, employees, reason_ids):
    for emp in employees:
        if not emp['terminated']:
            continue
        hired_at = conn.execute(
            text('SELECT hired_at FROM staff.employees WHERE id = :id'), {'id': emp['id']}
        ).scalar_one()
        terminated_at = min(hired_at + timedelta(days=random.randint(90, 1200)), date.today())
        conn.execute(
            text("""
                INSERT INTO staff.terminations (employee_id, terminated_at, reason_id)
                VALUES (:employee_id, :terminated_at, :reason_id)
            """),
            {
                'employee_id': emp['id'],
                'terminated_at': terminated_at,
                'reason_id': reason_ids[random.choice(TERMINATION_REASONS)],
            },
        )


def seed_leave_balances(conn, employees):
    current_year = date.today().year
    for emp in employees:
        for year in (current_year - 1, current_year):
            allocated = 24
            used = random.randint(0, allocated)
            conn.execute(
                text("""
                    INSERT INTO staff.leave_balances (employee_id, year, allocated_days, used_days)
                    VALUES (:employee_id, :year, :allocated_days, :used_days)
                """),
                {'employee_id': emp['id'], 'year': year, 'allocated_days': allocated, 'used_days': used},
            )


def main() -> None:
    with engine.begin() as conn:
        status_ids = seed_lookup(conn, 'employee_statuses', EMPLOYEE_STATUSES)
        reason_ids = seed_lookup(conn, 'employment_change_reasons', EMPLOYMENT_CHANGE_REASONS)
        type_ids = seed_lookup(conn, 'vacation_types', VACATION_TYPES)
        termination_reason_ids = seed_lookup(conn, 'termination_reasons', TERMINATION_REASONS)
        dept_ids = seed_departments(conn)
        pos_ids = seed_positions(conn)

        employees = seed_employees(conn, status_ids)
        seed_employment_changes(conn, employees, dept_ids, pos_ids, reason_ids)
        seed_salaries(conn, employees)
        seed_vacations(conn, employees, type_ids)
        seed_terminations(conn, employees, termination_reason_ids)
        seed_leave_balances(conn, employees)

    print(f'Seeded {len(employees)} employees into staff schema.')


if __name__ == '__main__':
    main()