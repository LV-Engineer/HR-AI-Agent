from app.reports import service as reports_module
from tests.conftest import _login, _sample_pdf_bytes


class TestListReports:
    def test_returns_reports_newest_first(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        report_path = reports_module.REPORTS_DIR / 'route_test_report.pdf'
        report_path.write_bytes(_sample_pdf_bytes())

        response = client.get('/reports', headers=headers)

        assert response.status_code == 200
        filenames = [r['filename'] for r in response.json()]
        assert 'route_test_report.pdf' in filenames

        report_path.unlink()

    def test_requires_authentication(self, client) -> None:
        response = client.get('/reports')

        assert response.status_code == 401


class TestViewReport:
    def test_returns_file_inline(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        report_path = reports_module.REPORTS_DIR / 'route_view_report.pdf'
        report_path.write_bytes(_sample_pdf_bytes())

        response = client.get('/reports/route_view_report.pdf', headers=headers)

        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert 'inline' in response.headers['content-disposition']

        report_path.unlink()

    def test_returns_404_for_unknown_file(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.get(
            '/reports/does_not_exist.pdf', headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.get('/reports/whatever.pdf')

        assert response.status_code == 401


class TestDeleteReport:
    def test_deletes_file(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}

        report_path = reports_module.REPORTS_DIR / 'route_delete_report.pdf'
        report_path.write_bytes(_sample_pdf_bytes())

        response = client.delete('/reports/route_delete_report.pdf', headers=headers)

        assert response.status_code == 204
        assert not report_path.exists()

    def test_returns_404_for_unknown_file(self, client, test_user) -> None:
        email, password = test_user
        tokens = _login(client, email, password)

        response = client.delete(
            '/reports/does_not_exist.pdf', headers={'Authorization': f'Bearer {tokens["access_token"]}'},
        )

        assert response.status_code == 404

    def test_requires_authentication(self, client) -> None:
        response = client.delete('/reports/whatever.pdf')

        assert response.status_code == 401
