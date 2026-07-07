"""
Pytest configuration and fixtures for openlca_ipc tests.

These fixtures provide a fully mocked olca_ipc.Client so the suite runs
without a live openLCA desktop instance.

The mock uses ``MagicMock(spec=ipc.Client)`` / ``MagicMock(spec=ipc.Result)``
so that any call to a method that does not exist on the real class raises
AttributeError immediately — the same error you'd get against a real server.
This prevents bugs where wrapper code calls a non-existent IPC method from
hiding behind silent mock fabrication.
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o
import olca_ipc as ipc


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Core fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ipc_client():
    """Mock olca_ipc.Client for testing without an openLCA server.

    Uses ``MagicMock(spec=ipc.Client)`` so that calls to methods that do not
    exist on the real client (e.g. the old ``lcia_process_contributions``)
    raise AttributeError rather than silently succeeding.

    ``get`` is wired with a side effect so requests for the Mass flow property
    and its unit group return sensible objects (the DataBuilder needs both to
    construct flows and exchanges).
    """
    mock_client = MagicMock(spec=ipc.Client)

    mass_prop = _make_mass_property()
    unit_group = _make_mass_unit_group()

    def _get(model_type, uid=None, *, name=None):
        if model_type is o.FlowProperty:
            return mass_prop
        if model_type is o.UnitGroup:
            return unit_group
        return None

    mock_client.get.side_effect = _get
    mock_client.get_descriptors.return_value = []
    mock_client.put.return_value = o.Ref(id="test-id", name="Test Object")
    mock_client.calculate.return_value = MagicMock(spec=ipc.Result)

    return mock_client


@pytest.fixture
def mock_result():
    """A spec'd mock of olca_ipc.Result.

    Methods that exist on the real Result (``get_total_impacts``,
    ``get_impact_contributions_of``, ``get_flow_impacts_of``, ``dispose``,
    ``wait_until_ready``, ``simulate_next``, …) are accessible.
    Methods that do NOT exist raise AttributeError.
    """
    result = MagicMock(spec=ipc.Result)
    result.get_total_impacts.return_value = []
    result.get_impact_contributions_of.return_value = []
    result.get_flow_impacts_of.return_value = []
    result.wait_until_ready.return_value = None
    result.simulate_next.return_value = MagicMock()
    result.dispose.return_value = None
    return result


# ---------------------------------------------------------------------------
# Domain fixtures
# ---------------------------------------------------------------------------

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
def sample_result(mock_result):
    """A spec'd calculation result.  Alias for ``mock_result``."""
    return mock_result


@pytest.fixture
def sample_impact_category():
    """An impact category reference."""
    return o.Ref(id="cat-123", name="Global warming")
