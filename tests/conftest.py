"""
Pytest configuration and fixtures for openlca_ipc tests.

These fixtures provide a fully mocked olca_ipc.Client so the suite runs
without a live openLCA desktop instance. The mock is configured to return
the Mass flow property and a kg unit, which several builders rely on.
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o


def _make_mass_property():
    """A Mass flow property pointing at a 'Units of mass' unit group."""
    prop = o.FlowProperty()
    prop.id = "mass-prop-id"
    prop.name = "Mass"
    prop.unit_group = o.Ref(id="unit-group-id", name="Units of mass")
    return prop


def _make_mass_unit_group():
    """A unit group whose reference unit is kg."""
    group = o.UnitGroup()
    group.id = "unit-group-id"
    group.name = "Units of mass"
    kg = o.Unit()
    kg.id = "kg-unit-id"
    kg.name = "kg"
    kg.conversion_factor = 1.0
    group.units = [kg]
    return group


@pytest.fixture
def mock_ipc_client():
    """Mock olca_ipc.Client for testing without an openLCA server.

    ``get`` is wired with a side effect so that requests for the Mass flow
    property and its unit group return sensible objects (the DataBuilder
    needs both to construct flows and exchanges).
    """
    mock_client = MagicMock()

    mass_prop = _make_mass_property()
    unit_group = _make_mass_unit_group()

    def _get(model_type, arg=None, *, name=None):
        if model_type is o.FlowProperty:
            return mass_prop
        if model_type is o.UnitGroup:
            return unit_group
        return None

    mock_client.get.side_effect = _get
    mock_client.get_descriptors.return_value = []
    mock_client.put.return_value = o.Ref(id="test-id", name="Test Object")
    mock_client.calculate.return_value = MagicMock()

    return mock_client


@pytest.fixture
def sample_flow():
    """Create a sample flow for testing."""
    flow = o.Flow()
    flow.id = "flow-123"
    flow.name = "Steel"
    flow.flow_type = o.FlowType.PRODUCT_FLOW
    return flow


@pytest.fixture
def sample_process():
    """Create a sample process for testing."""
    process = o.Process()
    process.id = "process-123"
    process.name = "Steel production"
    process.process_type = o.ProcessType.UNIT_PROCESS
    return process


@pytest.fixture
def sample_product_system():
    """Create a sample product system reference for testing."""
    return o.Ref(id="system-123", name="Steel system", ref_type=o.RefType.ProductSystem)


@pytest.fixture
def sample_impact_method():
    """Create a sample impact method for testing."""
    method = o.ImpactMethod()
    method.id = "method-123"
    method.name = "TRACI 2.1"
    return method


@pytest.fixture
def sample_result():
    """Create a sample calculation result for testing."""
    result = MagicMock()
    result.id = "result-123"
    return result
