from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from app.core.config import settings

REPORTS_DIR = Path(settings.reports_dir).resolve()

class ReportFile(NamedTuple):
    filename: str
    created_at: datetime

class ReportNotFoundError(Exception):
    pass

def resolve_report_path(filename: str) -> Path:
    file_path = (REPORTS_DIR / filename).resolve()
    if REPORTS_DIR not in file_path.parents or not file_path.is_file():
        raise ReportNotFoundError()
    return file_path

def list_reports() -> list[ReportFile]:
    reports = [
        ReportFile(filename=f.name, created_at=datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc))
        for f in REPORTS_DIR.glob('*.pdf')
    ]
    return sorted(reports, key=lambda r: r.created_at, reverse=True)

def delete_report(filename: str) -> None:
    file_path = resolve_report_path(filename)
    file_path.unlink()
