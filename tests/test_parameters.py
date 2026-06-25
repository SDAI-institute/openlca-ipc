"""
Tests for ParameterManager.
"""
import pytest
from unittest.mock import MagicMock, patch
import olca_schema as o
from openlca_ipc.parameters import ParameterManager


def _make_impact_value(name: str, amount: float) -> o.ImpactValue:
    return o.ImpactValue(
        impact_category=o.Ref(id=f"c-{name}", name=name),
        amount=amount,
    )


class TestParameterManager:

    def test_initialization(self, mock_ipc_client):
        pm = ParameterManager(mock_ipc_client)
        assert pm.client is mock_ipc_client

    # ------------------------------------------------------------------
    # create_parameter_redef
    # ------------------------------------------------------------------

    def test_create_parameter_redef_global(self, mock_ipc_client):
        pm = ParameterManager(mock_ipc_client)
        redef = pm.create_parameter_redef("transport_km", 500.0)

        assert isinstance(redef, o.ParameterRedef)
        assert redef.name == "transport_km"
        assert redef.value == 500.0
        assert redef.context is None

    def test_create_parameter_redef_with_context(self, mock_ipc_client):
        ctx = o.Ref(id="proc-1", name="Steel process")
        pm = ParameterManager(mock_ipc_client)
        redef = pm.create_parameter_redef("efficiency", 0.9, context=ctx)

        assert redef.context is ctx

    # ------------------------------------------------------------------
    # run_scenario_analysis
    # ------------------------------------------------------------------

    def test_run_scenario_analysis_iterates_values(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        mock_result.get_total_impacts.return_value = [
            _make_impact_value("GWP", 1.0)
        ]
        mock_ipc_client.calculate.return_value = mock_result

        pm = ParameterManager(mock_ipc_client)
        results = pm.run_scenario_analysis(
            system=sample_product_system,
            impact_method=sample_impact_method,
            parameter_name="distance",
            values=[100.0, 500.0],
        )

        assert set(results.keys()) == {100.0, 500.0}
        assert mock_ipc_client.calculate.call_count == 2

    def test_run_scenario_analysis_sets_parameter_in_setup(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        mock_result.get_total_impacts.return_value = []
        mock_ipc_client.calculate.return_value = mock_result

        pm = ParameterManager(mock_ipc_client)
        pm.run_scenario_analysis(
            system=sample_product_system,
            impact_method=sample_impact_method,
            parameter_name="my_param",
            values=[42.0],
        )

        setup: o.CalculationSetup = mock_ipc_client.calculate.call_args[0][0]
        assert len(setup.parameters) == 1
        assert setup.parameters[0].name == "my_param"
        assert setup.parameters[0].value == 42.0

    def test_run_scenario_analysis_disposes_each_result(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        mock_result.get_total_impacts.return_value = []
        mock_ipc_client.calculate.return_value = mock_result

        pm = ParameterManager(mock_ipc_client)
        pm.run_scenario_analysis(
            system=sample_product_system,
            impact_method=sample_impact_method,
            parameter_name="p",
            values=[1.0, 2.0, 3.0],
        )

        assert mock_result.dispose.call_count == 3

    def test_run_scenario_analysis_accepts_ref_method(
        self, mock_ipc_client, mock_result, sample_product_system
    ):
        """impact_method may be an o.Ref (no to_ref())."""
        mock_result.get_total_impacts.return_value = []
        mock_ipc_client.calculate.return_value = mock_result

        method_ref = o.Ref(id="m1", name="TRACI")
        pm = ParameterManager(mock_ipc_client)
        pm.run_scenario_analysis(
            system=sample_product_system,
            impact_method=method_ref,
            parameter_name="p",
            values=[1.0],
        )

        setup: o.CalculationSetup = mock_ipc_client.calculate.call_args[0][0]
        assert setup.impact_method == method_ref
