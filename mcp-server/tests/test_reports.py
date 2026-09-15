from pathlib import Path

import pytest

from app.core import reports as reports_module
from app.core.reports import generate_report

@pytest.fixture(autouse=True)
def _use_tmp_reports_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reports_module, 'REPORTS_DIR', tmp_path)

class TestGenerateReport:
    def test_creates_pdf_file(self) -> None:
        path = generate_report(
            title='Test Report',
            data=[{'department': 'IT', 'avg_salary': 45000}, {'department': 'HR', 'avg_salary': 32000}],
            summary='Test summary.'
        )

        pdf_path = Path(path)
        assert pdf_path.exists()
        assert pdf_path.suffix == '.pdf'
        assert pdf_path.read_bytes().startswith(b'%PDF')

    def test_works_without_chart(self) -> None:
        path = generate_report(
            title='No Chart Report',
            data=[{'note': 'free text row'}],
            summary='No numeric data here.',
            chart_type='none',
        )

        assert Path(path).exists()

    def test_works_with_empty_data(self) -> None:
        path = generate_report(title='Empty Report', data=[], summary='No data available.')

        assert Path(path).exists()

    def test_line_chart_type(self) -> None:
        path = generate_report(
            title='Trend Report',
            data=[{'month': 'Jan', 'hires': 3}, {'month': 'Feb', 'hires': 5}],
            summary='Hiring trend.',
            chart_type='line',
        )

        assert Path(path).exists()

    def test_skips_chart_when_data_has_no_label_column(self) -> None:
        path = generate_report(
            title='All Numeric',
            data=[{'x': 1, 'y': 2}, {'x': 3, 'y': 4}],
            summary='No categorical column here.',
        )
        assert Path(path).exists()