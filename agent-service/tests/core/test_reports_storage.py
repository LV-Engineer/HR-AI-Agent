import os
import time

import pytest

from app.core import reports as reports_module
from app.core.reports import ReportNotFoundError, delete_report, list_reports, resolve_report_path
from tests.conftest import _sample_pdf_bytes


class TestResolveReportPath:
    def test_returns_path_for_existing_file(self) -> None:
        report_path = reports_module.REPORTS_DIR / 'report_test.pdf'
        report_path.write_bytes(_sample_pdf_bytes())

        result = resolve_report_path('report_test.pdf')

        assert result == report_path
        report_path.unlink()

    def test_raises_for_missing_file(self) -> None:
        with pytest.raises(ReportNotFoundError):
            resolve_report_path('does_not_exist.pdf')

    def test_raises_for_path_traversal(self) -> None:
        with pytest.raises(ReportNotFoundError):
            resolve_report_path('../../etc/passwd')


class TestListReports:
    def test_returns_pdfs_newest_first(self) -> None:
        old_path = reports_module.REPORTS_DIR / 'old_report.pdf'
        new_path = reports_module.REPORTS_DIR / 'new_report.pdf'
        old_path.write_bytes(_sample_pdf_bytes())
        new_path.write_bytes(_sample_pdf_bytes())
        os.utime(old_path, (time.time() - 100, time.time() - 100))

        result = list_reports()

        names = [r.filename for r in result]
        assert names.index('new_report.pdf') < names.index('old_report.pdf')

        old_path.unlink()
        new_path.unlink()


class TestDeleteReport:
    def test_removes_file(self) -> None:
        report_path = reports_module.REPORTS_DIR / 'to_delete.pdf'
        report_path.write_bytes(_sample_pdf_bytes())

        delete_report('to_delete.pdf')

        assert not report_path.exists()

    def test_raises_for_missing_file(self) -> None:
        with pytest.raises(ReportNotFoundError):
            delete_report('does_not_exist.pdf')
