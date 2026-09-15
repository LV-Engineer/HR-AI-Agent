CREATE SCHEMA IF NOT EXISTS staff;

CREATE TABLE staff.employee_statuses (
    id   SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE
);

CREATE TABLE staff.employment_change_reasons (
    id   SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE
);

CREATE TABLE staff.vacation_types (
    id   SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE
);

CREATE TABLE staff.termination_reasons (
    id   SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE
);

CREATE TABLE staff.departments (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE staff.positions (
    id    SERIAL PRIMARY KEY,
    title TEXT NOT NULL UNIQUE
);

CREATE TABLE staff.employees (
    id          SERIAL PRIMARY KEY,
    last_name   TEXT NOT NULL,
    first_name  TEXT NOT NULL,
    middle_name TEXT,
    hired_at    DATE NOT NULL,
    status_id   INTEGER NOT NULL REFERENCES staff.employee_statuses(id),
    manager_id  INTEGER REFERENCES staff.employees(id)
);

CREATE TABLE staff.employment_changes (
    id             SERIAL PRIMARY KEY,
    employee_id    INTEGER NOT NULL REFERENCES staff.employees(id),
    department_id  INTEGER NOT NULL REFERENCES staff.departments(id),
    position_id    INTEGER NOT NULL REFERENCES staff.positions(id),
    effective_from DATE NOT NULL,
    reason_id      INTEGER REFERENCES staff.employment_change_reasons(id)
);

CREATE TABLE staff.salaries (
    id             SERIAL PRIMARY KEY,
    employee_id    INTEGER NOT NULL REFERENCES staff.employees(id),
    amount         NUMERIC(12,2) NOT NULL,
    effective_from DATE NOT NULL
);

CREATE TABLE staff.vacations (
    id          SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES staff.employees(id),
    type_id     INTEGER NOT NULL REFERENCES staff.vacation_types(id),
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL
);

CREATE TABLE staff.terminations (
    id            SERIAL PRIMARY KEY,
    employee_id   INTEGER NOT NULL REFERENCES staff.employees(id),
    terminated_at DATE NOT NULL,
    reason_id     INTEGER REFERENCES staff.termination_reasons(id)
);

CREATE TABLE staff.leave_balances (
    id             SERIAL PRIMARY KEY,
    employee_id    INTEGER NOT NULL REFERENCES staff.employees(id),
    year           INTEGER NOT NULL,
    allocated_days INTEGER NOT NULL,
    used_days      INTEGER NOT NULL DEFAULT 0
);