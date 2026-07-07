"""
Tests for UncertaintyAnalyzer.

The Monte Carlo flow uses:
  client.simulate(setup)       -> Result
  result.simulate_next()       -> o.ResultState
  result.get_total_impacts()   -> list[o.ImpactValue]  (after each next())
  result.dispose()             -> None  (always, via finally)
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, call, patch
import olca_schema as o
import olca_ipc as ipc
from openlca_ipc.uncertainty import UncertaintyAnalyzer, UncertaintyResult


def _make_impact_value(name: str, amount: float) -> o.ImpactValue:
    return o.ImpactValue(
        impact_category=o.Ref(id=f"c-{name}", name=name),
        amount=amount,
    )


class TestUncertaintyAnalyzer:

    def test_initialization(self, mock_ipc_client):
        ua = UncertaintyAnalyzer(mock_ipc_client)
        assert ua.client is mock_ipc_client

    # ------------------------------------------------------------------
    # run_monte_carlo
    # ------------------------------------------------------------------

    def test_run_monte_carlo_uses_simulate_not_simulator(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        """Must call client.simulate(), not the old client.simulator()."""
        mock_ipc_client.simulate.return_value = mock_result
        mock_result.get_total_impacts.return_value = [
            _make_impact_value("GWP", 1.0)
        ]

        ua = UncertaintyAnalyzer(mock_ipc_client)
        ua.run_monte_carlo(sample_product_system, sample_impact_method, iterations=3)

        mock_ipc_client.simulate.assert_called_once()
        # The old API (simulator / next_simulation / client.dispose) must NOT be called
        assert not hasattr(mock_ipc_client, 'simulator') or \
               not mock_ipc_client.simulator.called

    def test_run_monte_carlo_calls_simulate_next_n_times(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        mock_ipc_client.simulate.return_value = mock_result
        mock_result.get_total_impacts.return_value = [
            _make_impact_value("GWP", 1.0)
        ]

        ua = UncertaintyAnalyzer(mock_ipc_client)
        ua.run_monte_carlo(sample_product_system, sample_impact_method, iterations=5)

        assert mock_result.simulate_next.call_count == 5

    def test_run_monte_carlo_disposes_result_in_finally(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        """dispose() must be called even if an iteration raises."""
        mock_ipc_client.simulate.return_value = mock_result
        mock_result.simulate_next.side_effect = RuntimeError("network error")

        ua = UncertaintyAnalyzer(mock_ipc_client)
        with pytest.raises(RuntimeError):
            ua.run_monte_carlo(sample_product_system, sample_impact_method, iterations=3)

        mock_result.dispose.assert_called_once()

    def test_run_monte_carlo_returns_uncertainty_results(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        mock_ipc_client.simulate.return_value = mock_result
        # Vary GWP across 10 iterations
        gwp_values = [float(i + 1) for i in range(10)]
        mock_result.get_total_impacts.side_effect = [
            [_make_impact_value("GWP", v)] for v in gwp_values
        ]

        ua = UncertaintyAnalyzer(mock_ipc_client)
        results = ua.run_monte_carlo(
            sample_product_system, sample_impact_method, iterations=10
        )

        assert "GWP" in results
        ur = results["GWP"]
        assert isinstance(ur, UncertaintyResult)
        assert len(ur.values) == 10
        assert ur.mean == pytest.approx(np.mean(gwp_values))
        assert ur.std == pytest.approx(np.std(gwp_values))
        assert ur.median == pytest.approx(np.median(gwp_values))
        assert ur.percentile_5 == pytest.approx(np.percentile(gwp_values, 5))
        assert ur.percentile_95 == pytest.approx(np.percentile(gwp_values, 95))

    def test_run_monte_carlo_progress_callback(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        mock_ipc_client.simulate.return_value = mock_result
        mock_result.get_total_impacts.return_value = [
            _make_impact_value("GWP", 1.0)
        ]
        callback = MagicMock()

        ua = UncertaintyAnalyzer(mock_ipc_client)
        ua.run_monte_carlo(
            sample_product_system,
            sample_impact_method,
            iterations=200,
            progress_callback=callback,
        )

        # Called at 100 and 200
        assert callback.call_count == 2
        callback.assert_any_call(100, 200)
        callback.assert_any_call(200, 200)

    def test_run_monte_carlo_accepts_ref_method(
        self, mock_ipc_client, mock_result, sample_product_system
    ):
        """impact_method may be an o.Ref (has no to_ref())."""
        mock_ipc_client.simulate.return_value = mock_result
        mock_result.get_total_impacts.return_value = []

        method_ref = o.Ref(id="m1", name="TRACI")
        ua = UncertaintyAnalyzer(mock_ipc_client)
        ua.run_monte_carlo(sample_product_system, method_ref, iterations=1)

        setup: o.CalculationSetup = mock_ipc_client.simulate.call_args[0][0]
        assert setup.impact_method == method_ref

    # ------------------------------------------------------------------
    # compare_with_uncertainty
    # ------------------------------------------------------------------

    def test_compare_with_uncertainty_runs_two_simulations(
        self, mock_ipc_client, mock_result,
        sample_product_system, sample_impact_method
    ):
        mock_ipc_client.simulate.return_value = mock_result
        mock_result.get_total_impacts.return_value = [
            _make_impact_value("GWP", 1.0)
        ]

        system2 = o.Ref(id="sys-2", name="Alternative")
        ua = UncertaintyAnalyzer(mock_ipc_client)
        result = ua.compare_with_uncertainty(
            sample_product_system, system2, sample_impact_method, iterations=5
        )

        assert mock_ipc_client.simulate.call_count == 2
        assert "GWP" in result
        assert 'system1_mean' in result['GWP']
        assert 'system2_mean' in result['GWP']
        assert 'significantly_different' in result['GWP']
