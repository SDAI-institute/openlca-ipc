"""
Live integration tests for openlca-ipc against a real openLCA IPC server.

These tests require:
  1. openLCA desktop app running with a database open.
  2. IPC server started (Tools → Developer tools → IPC server).

Run:
    pytest -m live                           # default port 8080
    OLCA_IPC_PORT=9090 pytest -m live        # custom port

Tests are skipped by default and excluded from CI.
Tests may CREATE flows, processes, and product systems in the active database —
only use against a disposable/scratch database.
"""
from __future__ import annotations

import os
import time
import pytest
import olca_schema as o
from openlca_ipc import OLCAClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _port() -> int:
    return int(os.environ.get('OLCA_IPC_PORT', '8080'))


def _unique(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000) % 100_000}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def live_client():
    """Connect to a running openLCA IPC server for the duration of the module."""
    try:
        client = OLCAClient(port=_port())
    except ConnectionError as exc:
        pytest.skip(f"openLCA IPC server not available on port {_port()}: {exc}")
    yield client
    # No explicit close needed — ipc.Client has no close()


@pytest.fixture(scope='module')
def impact_method(live_client):
    """Return the first available impact method or skip if none exists."""
    for kws in (['TRACI'], ['ReCiPe'], ['CML'], ['EF'], ['IMPACT']):
        method = live_client.search.find_impact_method(kws)
        if method:
            return method
    pytest.skip("No impact method found in the active database")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.live
class TestLiveConnection:

    def test_connect(self, live_client):
        assert live_client is not None
        assert live_client.test_connection() is True

    def test_context_manager_exit_clean(self):
        """__exit__ must not raise even on a live client (which has no close())."""
        with OLCAClient(port=_port()) as client:
            assert client.test_connection() is True


@pytest.mark.live
class TestLiveSearch:

    def test_find_flows(self, live_client):
        for kws in (['steel'], ['water'], ['electricity'], ['carbon']):
            flows = live_client.search.find_flows(kws, max_results=3)
            if flows:
                assert all(isinstance(f, o.Ref) for f in flows)
                return
        pytest.skip("No matching flows found in the active database")

    def test_find_processes(self, live_client):
        for kws in (['production'], ['process'], ['manufacturing']):
            procs = live_client.search.find_processes(kws, max_results=3)
            if procs:
                assert all(isinstance(p, o.Ref) for p in procs)
                return
        pytest.skip("No matching processes found")

    def test_find_impact_method(self, impact_method):
        assert impact_method is not None
        assert isinstance(impact_method, o.ImpactMethod)

    def test_find_providers(self, live_client):
        for kws in (['steel'], ['water'], ['electricity']):
            flow = live_client.search.find_flow(kws)
            if flow:
                providers = live_client.search.find_providers(flow)
                assert isinstance(providers, list)
                return
        pytest.skip("No flow with providers found")


@pytest.mark.live
class TestLiveDataCreation:

    def test_create_product_flow(self, live_client):
        name = _unique("test_flow")
        flow = live_client.data.create_product_flow(name, description="Integration test flow")
        assert flow is not None
        assert flow.id is not None

    def test_create_process_and_system(self, live_client):
        """Full round-trip: flow → exchange → process → product system."""
        flow = live_client.data.create_product_flow(_unique("tf"))
        exchange = live_client.data.create_exchange(
            flow=flow, amount=1.0, is_input=False, is_quantitative_reference=True
        )
        process = live_client.data.create_process(_unique("tp"), exchanges=[exchange])
        assert process.id is not None

        system_ref = live_client.systems.create_product_system(process)
        assert system_ref is not None
        assert isinstance(system_ref, o.Ref)


@pytest.mark.live
class TestLiveCalculation:

    @pytest.fixture(scope='class')
    @classmethod
    def live_system_ref(cls, live_client):
        """Return an existing product system or create one from first process."""
        systems = live_client.client.get_descriptors(o.ProductSystem)
        if systems:
            return systems[0]
        procs = live_client.client.get_descriptors(o.Process)
        if not procs:
            pytest.skip("No processes in database to build a product system")
        proc = live_client.client.get(o.Process, procs[0].id)
        ref = live_client.systems.create_product_system(proc)
        if not ref:
            pytest.skip("Could not create a product system")
        return ref

    def test_simple_calculation(self, live_client, live_system_ref, impact_method):
        result = live_client.calculate.simple_calculation(
            system=live_system_ref, impact_method=impact_method, amount=1.0
        )
        try:
            assert result is not None
            impacts = live_client.results.get_total_impacts(result)
            assert isinstance(impacts, list)
        finally:
            result.dispose()

    def test_get_total_impacts(self, live_client, live_system_ref, impact_method):
        result = live_client.calculate.simple_calculation(
            system=live_system_ref, impact_method=impact_method
        )
        try:
            impacts = live_client.results.get_total_impacts(result)
            if impacts:
                for imp in impacts[:3]:
                    assert 'name' in imp
                    assert 'amount' in imp
                    assert isinstance(imp['amount'], float)
        finally:
            result.dispose()

    def test_process_contributions(self, live_client, live_system_ref, impact_method):
        result = live_client.calculate.simple_calculation(
            system=live_system_ref, impact_method=impact_method
        )
        try:
            impacts = live_client.results.get_total_impacts(result)
            if not impacts:
                pytest.skip("No impacts returned")
            cat_ref = impacts[0]['category']
            contribs = live_client.contributions.get_process_contributions(
                result, cat_ref, min_share=0
            )
            assert isinstance(contribs, list)
        finally:
            result.dispose()

    def test_flow_contributions(self, live_client, live_system_ref, impact_method):
        result = live_client.calculate.simple_calculation(
            system=live_system_ref, impact_method=impact_method
        )
        try:
            impacts = live_client.results.get_total_impacts(result)
            if not impacts:
                pytest.skip("No impacts returned")
            cat_ref = impacts[0]['category']
            contribs = live_client.contributions.get_flow_contributions(
                result, cat_ref, min_share=0
            )
            assert isinstance(contribs, list)
        finally:
            result.dispose()

    def test_result_dispose(self, live_client, live_system_ref, impact_method):
        """result.dispose() must not raise."""
        result = live_client.calculate.simple_calculation(
            system=live_system_ref, impact_method=impact_method
        )
        result.dispose()  # should not raise
