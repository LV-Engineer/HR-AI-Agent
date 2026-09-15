from unittest.mock import MagicMock

import pytest

from app import server as server_module


class TestToolWiring:
    def test_get_schema_delegates_to_get_schema_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock = MagicMock(return_value={'staff': {}})
        monkeypatch.setattr(server_module, 'get_schema_info', mock)

        result = server_module.get_schema()

        mock.assert_called_once_with()
        assert result == {'staff': {}}

    def test_query_database_delegates_to_run_query(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock = MagicMock(return_value=[{'id': 1}])
        monkeypatch.setattr(server_module, 'run_query', mock)

        result = server_module.query_database('SELECT 1')

        mock.assert_called_once_with('SELECT 1')
        assert result == [{'id': 1}]

    def test_search_hr_policy_delegates_to_search_hr_policies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock = MagicMock(return_value=[{'title': 'Policy'}])
        monkeypatch.setattr(server_module, 'search_hr_policies', mock)

        result = server_module.search_hr_policy('vacation')

        mock.assert_called_once_with('vacation')
        assert result == [{'title': 'Policy'}]

    def test_match_candidate_delegates_to_matching_logic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock = MagicMock(return_value={'distance': 0.1})
        monkeypatch.setattr(server_module, 'match_candidate_logic', mock)

        result = server_module.match_candidate('cv-1', 5)

        mock.assert_called_once_with('cv-1', 5)
        assert result == {'distance': 0.1}

    def test_generate_report_delegates_to_reports_logic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock = MagicMock(return_value='/app/storage/reports/report.pdf')
        monkeypatch.setattr(server_module, 'generate_report_logic', mock)

        result = server_module.generate_report('Title', [{'a': 1}], 'Summary', 'line')

        mock.assert_called_once_with('Title', [{'a': 1}], 'Summary', 'line')
        assert result == '/app/storage/reports/report.pdf'
