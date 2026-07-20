"""
Tests for ResultsAnalyzer.
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o
from openlca_ipc.results import ResultsAnalyzer


def _make_impact_value(cat_name: str, amount: float) -> o.ImpactValue:
    cat = o.Ref(id=f"cat-{cat_name}", name=cat_name)
    return o.ImpactValue(impact_category=cat, amount=amount)


class TestResultsAnalyzer:

    def test_initialization(self, mock_ipc_client):
        ra = ResultsAnalyzer(mock_ipc_client)
        assert ra.client is mock_ipc_client

    def test_get_total_impacts_returns_dicts(self, mock_ipc_client, mock_result):
        mock_result.get_total_impacts.return_value = [
            _make_impact_value("Global warming", 2.5),
            _make_impact_value("Acidification", 0.3),
        ]

        ra = ResultsAnalyzer(mock_ipc_client)
        impacts = ra.get_total_impacts(mock_result)

        assert len(impacts) == 2
        assert impacts[0]['name'] == "Global warming"
        assert impacts[0]['amount'] == 2.5
        assert 'category' in impacts[0]
        assert 'unit' in impacts[0]

    def test_get_total_impacts_handles_zero_amount(self, mock_ipc_client, mock_result):
        mock_result.get_total_impacts.return_value = [
            _make_impact_value("Eutrophication", 0.0),
        ]

        ra = ResultsAnalyzer(mock_ipc_client)
        impacts = ra.get_total_impacts(mock_result)

        assert impacts[0]['amount'] == 0.0

    def test_get_total_impacts_returns_empty_on_error(self, mock_ipc_client, mock_result):
        mock_result.get_total_impacts.side_effect = RuntimeError("rpc error")

        ra = ResultsAnalyzer(mock_ipc_client)
        impacts = ra.get_total_impacts(mock_result)

        assert impacts == []

    def test_get_total_impacts_none_amount_becomes_zero(self, mock_ipc_client, mock_result):
        """An ImpactValue with amount=None should produce 0.0, not crash."""
        iv = o.ImpactValue(impact_category=o.Ref(id="c1", name="X"), amount=None)
        mock_result.get_total_impacts.return_value = [iv]

        ra = ResultsAnalyzer(mock_ipc_client)
        impacts = ra.get_total_impacts(mock_result)

        assert impacts[0]['amount'] == 0.0
