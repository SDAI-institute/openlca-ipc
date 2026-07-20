"""
Tests for openlca_ipc.diagnostics.check_result_consistency.
"""
import olca_schema as o
from openlca_ipc.diagnostics import check_result_consistency


def _tfv(amount, name="p"):
    return o.TechFlowValue(
        amount=amount,
        tech_flow=o.TechFlow(provider=o.Ref(id=name, name=name)),
    )


class TestCheckResultConsistency:

    def test_consistent_result_has_no_warnings(self, mock_result):
        cat = o.Ref(id="GW", name="Global warming")
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(impact_category=cat, amount=10.0)
        ]
        mock_result.get_impact_contributions_of.return_value = [
            _tfv(6.0, "a"), _tfv(4.0, "b"),
        ]
        assert check_result_consistency(mock_result) == []

    def test_inconsistent_contributions_warn(self, mock_result):
        cat = o.Ref(id="GW", name="Global warming")
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(impact_category=cat, amount=10.0)
        ]
        mock_result.get_impact_contributions_of.return_value = [_tfv(2.0, "a")]
        warns = check_result_consistency(mock_result)
        assert len(warns) == 1
        assert "Global warming" in warns[0]

    def test_total_impacts_failure_reported(self, mock_result):
        mock_result.get_total_impacts.side_effect = RuntimeError("boom")
        warns = check_result_consistency(mock_result)
        assert warns and "could not read total impacts" in warns[0]

    def test_contribution_read_failure_reported(self, mock_result):
        cat = o.Ref(id="GW", name="Global warming")
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(impact_category=cat, amount=10.0)
        ]
        mock_result.get_impact_contributions_of.side_effect = RuntimeError("x")
        warns = check_result_consistency(mock_result)
        assert warns and "could not read contributions" in warns[0]

    def test_zero_total_within_abs_tol(self, mock_result):
        cat = o.Ref(id="GW", name="Global warming")
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(impact_category=cat, amount=0.0)
        ]
        mock_result.get_impact_contributions_of.return_value = []
        assert check_result_consistency(mock_result) == []
