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

    # A process context makes the parameter resolvable (local parameter), so
    # the no-op guard is satisfied without needing a global parameter.
    _CTX = o.Ref(id="proc-1", name="owning process")

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
            context=self._CTX,
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
            context=self._CTX,
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
            context=self._CTX,
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
            context=self._CTX,
        )

        setup: o.CalculationSetup = mock_ipc_client.calculate.call_args[0][0]
        assert setup.impact_method == method_ref

    # ------------------------------------------------------------------
    # no-op guard (v0.4.1): unknown parameter must fail loudly
    # ------------------------------------------------------------------

    def test_run_scenario_analysis_raises_for_unknown_parameter(
        self, mock_ipc_client, sample_product_system, sample_impact_method
    ):
        """Without a context and with no matching global parameter, the scenario
        would silently vary nothing — so it must raise instead."""
        mock_ipc_client.get_descriptors.return_value = []  # no global parameters

        pm = ParameterManager(mock_ipc_client)
        with pytest.raises(ValueError, match="not found as a global"):
            pm.run_scenario_analysis(
                system=sample_product_system,
                impact_method=sample_impact_method,
                parameter_name="does_not_exist",
                values=[1.0, 2.0],
            )
        mock_ipc_client.calculate.assert_not_called()

    def test_run_scenario_analysis_accepts_global_parameter(
        self, mock_ipc_client, mock_result, sample_product_system, sample_impact_method
    ):
        """A matching global parameter satisfies the guard without a context."""
        mock_ipc_client.get_descriptors.return_value = [
            o.Ref(id="p-glob", name="distance")
        ]
        mock_result.get_total_impacts.return_value = []
        mock_ipc_client.calculate.return_value = mock_result

        pm = ParameterManager(mock_ipc_client)
        results = pm.run_scenario_analysis(
            system=sample_product_system,
            impact_method=sample_impact_method,
            parameter_name="distance",
            values=[1.0],
        )
        assert set(results.keys()) == {1.0}

    def test_find_global_parameter(self, mock_ipc_client):
        mock_ipc_client.get_descriptors.return_value = [
            o.Ref(id="p1", name="Distance"), o.Ref(id="p2", name="efficiency"),
        ]
        pm = ParameterManager(mock_ipc_client)
        assert pm.find_global_parameter("distance").id == "p1"   # case-insensitive
        assert pm.find_global_parameter("missing") is None
