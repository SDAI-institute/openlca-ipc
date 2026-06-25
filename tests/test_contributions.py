"""
Tests for ContributionAnalyzer.

The ContributionAnalyzer uses the Result object API:
  - result.get_impact_contributions_of(impact_category) -> list[o.TechFlowValue]
  - result.get_flow_impacts_of(impact_category)         -> list[o.EnviFlowValue]
  - result.get_total_impacts()                           -> list[o.ImpactValue]

Tests verify the correct methods are called and that ContributionItem
objects are built properly.
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o
from openlca_ipc.contributions import ContributionAnalyzer, ContributionItem


def _make_tech_flow_value(process_name: str, amount: float) -> o.TechFlowValue:
    provider = o.Ref(id=f"p-{process_name}", name=process_name)
    tech_flow = o.TechFlow(provider=provider)
    return o.TechFlowValue(tech_flow=tech_flow, amount=amount)


def _make_envi_flow_value(flow_name: str, amount: float) -> o.EnviFlowValue:
    flow_ref = o.Ref(id=f"f-{flow_name}", name=flow_name)
    envi_flow = o.EnviFlow(flow=flow_ref)
    return o.EnviFlowValue(envi_flow=envi_flow, amount=amount)


def _make_impact_value(cat_id: str, cat_name: str, amount: float) -> o.ImpactValue:
    cat = o.Ref(id=cat_id, name=cat_name)
    return o.ImpactValue(impact_category=cat, amount=amount)


class TestContributionAnalyzer:

    def test_initialization(self, mock_ipc_client):
        ca = ContributionAnalyzer(mock_ipc_client)
        assert ca.client is mock_ipc_client

    # ------------------------------------------------------------------
    # get_process_contributions
    # ------------------------------------------------------------------

    def test_get_process_contributions_calls_correct_api(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        """Must call result.get_impact_contributions_of(), NOT any client method."""
        mock_result.get_impact_contributions_of.return_value = []
        mock_result.get_total_impacts.return_value = []

        ca = ContributionAnalyzer(mock_ipc_client)
        ca.get_process_contributions(mock_result, sample_impact_category)

        mock_result.get_impact_contributions_of.assert_called_once_with(
            sample_impact_category
        )

    def test_get_process_contributions_returns_items(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        raw = [
            _make_tech_flow_value("Steel mill", 2.0),
            _make_tech_flow_value("Transport", 0.5),
        ]
        mock_result.get_impact_contributions_of.return_value = raw
        # total = 2.5 kg CO2 eq
        mock_result.get_total_impacts.return_value = [
            _make_impact_value(sample_impact_category.id, sample_impact_category.name, 2.5)
        ]

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_process_contributions(mock_result, sample_impact_category, min_share=0)

        assert len(items) == 2
        assert items[0].name == "Steel mill"
        assert items[0].amount == 2.0
        assert abs(items[0].share - 0.8) < 1e-9
        assert items[0].ref.name == "Steel mill"

    def test_get_process_contributions_sorted_by_amount(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        raw = [
            _make_tech_flow_value("Small", 0.1),
            _make_tech_flow_value("Large", 5.0),
        ]
        mock_result.get_impact_contributions_of.return_value = raw
        mock_result.get_total_impacts.return_value = [
            _make_impact_value(sample_impact_category.id, sample_impact_category.name, 5.1)
        ]

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_process_contributions(mock_result, sample_impact_category, min_share=0)

        assert items[0].name == "Large"

    def test_get_process_contributions_min_share_filters(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        raw = [
            _make_tech_flow_value("Big", 9.0),
            _make_tech_flow_value("Tiny", 0.001),
        ]
        mock_result.get_impact_contributions_of.return_value = raw
        mock_result.get_total_impacts.return_value = [
            _make_impact_value(sample_impact_category.id, sample_impact_category.name, 9.001)
        ]

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_process_contributions(
            mock_result, sample_impact_category, min_share=0.01
        )

        assert len(items) == 1
        assert items[0].name == "Big"

    def test_get_process_contributions_returns_empty_on_error(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        mock_result.get_impact_contributions_of.side_effect = RuntimeError("rpc error")

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_process_contributions(mock_result, sample_impact_category)

        assert items == []

    # ------------------------------------------------------------------
    # get_flow_contributions
    # ------------------------------------------------------------------

    def test_get_flow_contributions_calls_correct_api(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        mock_result.get_flow_impacts_of.return_value = []
        mock_result.get_total_impacts.return_value = []

        ca = ContributionAnalyzer(mock_ipc_client)
        ca.get_flow_contributions(mock_result, sample_impact_category)

        mock_result.get_flow_impacts_of.assert_called_once_with(sample_impact_category)

    def test_get_flow_contributions_returns_items(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        raw = [
            _make_envi_flow_value("CO2", 3.0),
            _make_envi_flow_value("CH4", 0.5),
        ]
        mock_result.get_flow_impacts_of.return_value = raw
        mock_result.get_total_impacts.return_value = [
            _make_impact_value(sample_impact_category.id, sample_impact_category.name, 3.5)
        ]

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_flow_contributions(mock_result, sample_impact_category, min_share=0)

        assert len(items) == 2
        assert items[0].name == "CO2"
        assert abs(items[0].share - (3.0 / 3.5)) < 1e-9
        assert items[0].ref.name == "CO2"

    def test_get_flow_contributions_returns_empty_on_error(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        mock_result.get_flow_impacts_of.side_effect = RuntimeError("fail")

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_flow_contributions(mock_result, sample_impact_category)

        assert items == []

    # ------------------------------------------------------------------
    # get_top_contributors
    # ------------------------------------------------------------------

    def test_get_top_contributors_process(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        raw = [_make_tech_flow_value(f"P{i}", float(10 - i)) for i in range(8)]
        mock_result.get_impact_contributions_of.return_value = raw
        mock_result.get_total_impacts.return_value = [
            _make_impact_value(sample_impact_category.id, sample_impact_category.name, 52.0)
        ]

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_top_contributors(mock_result, sample_impact_category, n=5)

        assert len(items) == 5

    def test_get_top_contributors_flow(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        raw = [_make_envi_flow_value(f"F{i}", float(i + 1)) for i in range(4)]
        mock_result.get_flow_impacts_of.return_value = raw
        mock_result.get_total_impacts.return_value = [
            _make_impact_value(sample_impact_category.id, sample_impact_category.name, 10.0)
        ]

        ca = ContributionAnalyzer(mock_ipc_client)
        items = ca.get_top_contributors(
            mock_result, sample_impact_category, n=3, contribution_type='flow'
        )

        assert len(items) == 3

    # ------------------------------------------------------------------
    # get_contribution_summary
    # ------------------------------------------------------------------

    def test_get_contribution_summary_uses_all_categories(
        self, mock_ipc_client, mock_result
    ):
        cat1 = o.Ref(id="c1", name="GWP")
        cat2 = o.Ref(id="c2", name="AP")
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(impact_category=cat1, amount=1.0),
            o.ImpactValue(impact_category=cat2, amount=0.5),
        ]
        mock_result.get_impact_contributions_of.return_value = []

        ca = ContributionAnalyzer(mock_ipc_client)
        summary = ca.get_contribution_summary(mock_result)

        assert "GWP" in summary
        assert "AP" in summary

    def test_get_contribution_summary_with_explicit_categories(
        self, mock_ipc_client, mock_result, sample_impact_category
    ):
        mock_result.get_impact_contributions_of.return_value = []
        mock_result.get_total_impacts.return_value = [
            _make_impact_value(
                sample_impact_category.id, sample_impact_category.name, 1.0
            )
        ]

        ca = ContributionAnalyzer(mock_ipc_client)
        summary = ca.get_contribution_summary(mock_result, [sample_impact_category])

        assert sample_impact_category.name in summary
