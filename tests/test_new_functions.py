"""
Tests for the v0.4 additive LCA functions:
 - ContributionAnalyzer.get_contribution_tree
 - ResultsAnalyzer.get_inventory / normalized / weighted / requirements / sankey
 - CalculationManager.compare_systems
 - SearchUtils.get_by_name
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o
import olca_ipc as ipc

from openlca_ipc.contributions import ContributionAnalyzer
from openlca_ipc.results import ResultsAnalyzer
from openlca_ipc.calculations import CalculationManager
from openlca_ipc.search import SearchUtils


# ---------------------------------------------------------------------------
# Contribution tree
# ---------------------------------------------------------------------------

class TestContributionTree:

    def _wire_total(self, mock_result, total):
        cat = o.Ref(id="GW", name="Global warming")
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(impact_category=cat, amount=total)
        ]
        return cat

    def test_builds_nested_tree(self, mock_ipc_client, mock_result):
        cat = self._wire_total(mock_result, 100.0)
        tf_a = o.TechFlow(provider=o.Ref(id="a", name="A"))
        tf_b = o.TechFlow(provider=o.Ref(id="b", name="B"))

        def upstream(category, path):
            if len(path) == 0:
                return [o.UpstreamNode(result=100.0, direct_contribution=40.0, tech_flow=tf_a)]
            if len(path) == 1:
                return [o.UpstreamNode(result=60.0, direct_contribution=60.0, tech_flow=tf_b)]
            return []

        mock_result.get_upstream_impacts_of.side_effect = upstream

        tree = ContributionAnalyzer(mock_ipc_client).get_contribution_tree(
            mock_result, cat, max_depth=3, min_share=0.0
        )
        assert len(tree) == 1
        root = tree[0]
        assert root.name == "A"
        assert root.amount == 100.0
        assert abs(root.share - 1.0) < 1e-9
        assert root.direct == 40.0
        assert len(root.children) == 1
        assert root.children[0].name == "B"
        assert root.children[0].children == []  # max_depth stops recursion

    def test_max_depth_one_has_no_children(self, mock_ipc_client, mock_result):
        cat = self._wire_total(mock_result, 100.0)
        tf_a = o.TechFlow(provider=o.Ref(id="a", name="A"))
        mock_result.get_upstream_impacts_of.return_value = [
            o.UpstreamNode(result=100.0, direct_contribution=100.0, tech_flow=tf_a)
        ]
        tree = ContributionAnalyzer(mock_ipc_client).get_contribution_tree(
            mock_result, cat, max_depth=1, min_share=0.0
        )
        assert len(tree) == 1
        assert tree[0].children == []

    def test_min_share_prunes_small_branches(self, mock_ipc_client, mock_result):
        cat = self._wire_total(mock_result, 100.0)
        tf = o.TechFlow(provider=o.Ref(id="a", name="A"))
        # node result 2.0 -> share 0.02, below min_share 0.05 -> pruned
        mock_result.get_upstream_impacts_of.return_value = [
            o.UpstreamNode(result=2.0, direct_contribution=2.0, tech_flow=tf)
        ]
        tree = ContributionAnalyzer(mock_ipc_client).get_contribution_tree(
            mock_result, cat, max_depth=3, min_share=0.05
        )
        assert tree == []

    def test_error_returns_empty(self, mock_ipc_client, mock_result):
        cat = self._wire_total(mock_result, 100.0)
        mock_result.get_upstream_impacts_of.side_effect = RuntimeError("x")
        assert ContributionAnalyzer(mock_ipc_client).get_contribution_tree(
            mock_result, cat
        ) == []


# ---------------------------------------------------------------------------
# Results: inventory / normalized / weighted / requirements / sankey
# ---------------------------------------------------------------------------

class TestResultsV04:

    def test_get_inventory_sorts_and_flags_direction(self, mock_ipc_client, mock_result):
        out = o.EnviFlowValue(
            amount=3.0, envi_flow=o.EnviFlow(flow=o.Ref(id="co2", name="CO2"), is_input=False)
        )
        inp = o.EnviFlowValue(
            amount=5.0, envi_flow=o.EnviFlow(flow=o.Ref(id="o2", name="O2"), is_input=True)
        )
        mock_result.get_total_flows.return_value = [out, inp]
        ra = ResultsAnalyzer(mock_ipc_client)

        inv = ra.get_inventory(mock_result)
        assert [f["name"] for f in inv] == ["O2", "CO2"]  # sorted by abs amount
        assert inv[0]["is_input"] is True

        assert [f["name"] for f in ra.get_inventory(mock_result, direction="output")] == ["CO2"]
        assert [f["name"] for f in ra.get_inventory(mock_result, direction="input")] == ["O2"]

    def test_get_inventory_error_returns_empty(self, mock_ipc_client, mock_result):
        mock_result.get_total_flows.side_effect = RuntimeError("x")
        assert ResultsAnalyzer(mock_ipc_client).get_inventory(mock_result) == []

    def test_normalized_and_weighted(self, mock_ipc_client, mock_result):
        cat = o.Ref(id="c", name="GW")
        mock_result.get_normalized_impacts.return_value = [
            o.ImpactValue(impact_category=cat, amount=0.5)
        ]
        mock_result.get_weighted_impacts.return_value = [
            o.ImpactValue(impact_category=cat, amount=0.25)
        ]
        ra = ResultsAnalyzer(mock_ipc_client)
        assert ra.get_normalized_impacts(mock_result)[0]["amount"] == 0.5
        assert ra.get_weighted_impacts(mock_result)[0]["amount"] == 0.25

    def test_total_requirements(self, mock_ipc_client, mock_result):
        tfv = o.TechFlowValue(
            amount=2.0,
            tech_flow=o.TechFlow(
                provider=o.Ref(id="p", name="Proc"), flow=o.Ref(id="f", name="Flow")
            ),
        )
        mock_result.get_total_requirements.return_value = [tfv]
        reqs = ResultsAnalyzer(mock_ipc_client).get_total_requirements(mock_result)
        assert reqs[0]["process"] == "Proc"
        assert reqs[0]["flow"] == "Flow"
        assert reqs[0]["amount"] == 2.0

    def test_sankey_builds_request_and_returns_dict(self, mock_ipc_client, mock_result):
        graph = o.SankeyGraph(nodes=[], edges=[], root_index=0)
        mock_result.get_sankey_graph.return_value = graph
        cat = o.Ref(id="c", name="GW")
        d = ResultsAnalyzer(mock_ipc_client).get_sankey(mock_result, cat, max_nodes=10)
        assert isinstance(d, dict)
        request = mock_result.get_sankey_graph.call_args[0][0]
        assert request.impact_category is cat
        assert request.max_nodes == 10

    def test_sankey_error_returns_empty_dict(self, mock_ipc_client, mock_result):
        mock_result.get_sankey_graph.side_effect = RuntimeError("x")
        assert ResultsAnalyzer(mock_ipc_client).get_sankey(
            mock_result, o.Ref(id="c", name="GW")
        ) == {}


# ---------------------------------------------------------------------------
# compare_systems
# ---------------------------------------------------------------------------

class TestCompareSystems:

    def _result(self, amount):
        r = MagicMock(spec=ipc.Result)
        r.get_total_impacts.return_value = [
            o.ImpactValue(impact_category=o.Ref(id="c", name="GW"), amount=amount)
        ]
        r.wait_until_ready.return_value = None
        r.dispose.return_value = None
        return r

    def test_compare_two_systems(self, mock_ipc_client):
        r1, r2 = self._result(10.0), self._result(8.0)
        mock_ipc_client.calculate.side_effect = [r1, r2]
        cm = CalculationManager(mock_ipc_client)

        comp = cm.compare_systems(
            o.Ref(id="s1", name="S1"),
            o.Ref(id="s2", name="S2"),
            o.Ref(id="m", name="EF"),
        )
        assert comp["GW"]["system1"] == 10.0
        assert comp["GW"]["system2"] == 8.0
        assert comp["GW"]["difference"] == -2.0
        assert comp["GW"]["percent_diff"] == pytest.approx(-20.0)
        r1.dispose.assert_called_once()
        r2.dispose.assert_called_once()


# ---------------------------------------------------------------------------
# get_by_name
# ---------------------------------------------------------------------------

class TestGetByName:

    def test_delegates_to_find(self, mock_ipc_client):
        ref = o.Ref(id="x", name="Steel")
        mock_ipc_client.find.return_value = ref
        su = SearchUtils(mock_ipc_client)
        assert su.get_by_name(o.Flow, "Steel") is ref
        mock_ipc_client.find.assert_called_once_with(o.Flow, "Steel")

    def test_error_returns_none(self, mock_ipc_client):
        mock_ipc_client.find.side_effect = RuntimeError("x")
        assert SearchUtils(mock_ipc_client).get_by_name(o.Flow, "Steel") is None
