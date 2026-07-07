"""
Live validation tests for result accuracy & reliability.

Gated behind @pytest.mark.live (deselected by default). Requires a running
openLCA IPC server with a database open on OLCA_IPC_PORT (default 8080).

These tests build/load a product system, run a real calculation, and assert
that the wrapper's parsed results are internally consistent and faithful to
openLCA's own values:
  - wrapper get_total_impacts == raw Result.get_total_impacts (no value drift)
  - per-category process contributions sum to the category total
  - the contribution-tree root equals the category total
  - the inventory is non-empty
  - check_result_consistency reports no issues
"""
from __future__ import annotations

import os
import pytest
import olca_schema as o

from openlca_ipc import OLCAClient
from openlca_ipc.diagnostics import check_result_consistency

REL_TOL = 1e-3


def _port() -> int:
    return int(os.environ.get("OLCA_IPC_PORT", "8080"))


@pytest.fixture(scope="module")
def live_client():
    try:
        client = OLCAClient(port=_port())
    except ConnectionError as exc:
        pytest.skip(f"openLCA IPC server not available on port {_port()}: {exc}")
    yield client


@pytest.fixture(scope="module")
def impact_method(live_client):
    for kws in (["TRACI"], ["ReCiPe"], ["CML"], ["EF"], ["IMPACT"]):
        method = live_client.search.find_impact_method(kws)
        if method:
            return method
    pytest.skip("No impact method found in the active database")


@pytest.fixture(scope="module")
def computed(live_client, impact_method):
    """Return (result, top_category_ref) for a real calculation, disposed at teardown."""
    systems = live_client.client.get_descriptors(o.ProductSystem)
    if systems:
        system_ref = systems[0]
    else:
        procs = live_client.client.get_descriptors(o.Process)
        if not procs:
            pytest.skip("No processes in database to build a product system")
        proc = live_client.client.get(o.Process, procs[0].id)
        system_ref = live_client.systems.create_product_system(proc)
        if not system_ref:
            pytest.skip("Could not create a product system")

    result = live_client.calculate.simple_calculation(
        system=system_ref, impact_method=impact_method
    )
    impacts = live_client.results.get_total_impacts(result)
    if not impacts:
        result.dispose()
        pytest.skip("Calculation produced no impacts")
    top = max(impacts, key=lambda i: abs(i["amount"]))
    yield result, top["category"]
    result.dispose()


@pytest.mark.live
class TestResultValidation:

    def test_wrapper_totals_match_raw(self, live_client, computed):
        result, _ = computed
        wrapper = {
            i["name"]: i["amount"] for i in live_client.results.get_total_impacts(result)
        }
        raw = {
            iv.impact_category.name: (iv.amount or 0.0)
            for iv in result.get_total_impacts()
            if iv.impact_category
        }
        assert set(wrapper) == set(raw)
        for name, amount in raw.items():
            tol = max(1e-12, REL_TOL * abs(amount))
            assert abs(wrapper[name] - amount) <= tol

    def test_contributions_sum_to_total(self, live_client, computed):
        result, cat = computed
        total = next(
            i["amount"]
            for i in live_client.results.get_total_impacts(result)
            if i["category"].id == cat.id
        )
        contribs = live_client.contributions.get_process_contributions(
            result, cat, min_share=0
        )
        if not contribs:
            pytest.skip("No process contributions for top category")
        csum = sum(c.amount for c in contribs)
        tol = max(1e-9, REL_TOL * abs(total))
        assert abs(csum - total) <= tol

    def test_tree_root_matches_total(self, live_client, computed):
        result, cat = computed
        total = next(
            i["amount"]
            for i in live_client.results.get_total_impacts(result)
            if i["category"].id == cat.id
        )
        tree = live_client.contributions.get_contribution_tree(
            result, cat, max_depth=1, min_share=0
        )
        if not tree:
            pytest.skip("No upstream tree for top category")
        root_total = sum(n.amount for n in tree)
        tol = max(1e-9, REL_TOL * abs(total))
        assert abs(root_total - total) <= tol

    def test_inventory_non_empty(self, live_client, computed):
        result, _ = computed
        inventory = live_client.results.get_inventory(result)
        assert isinstance(inventory, list)
        assert len(inventory) > 0

    def test_consistency_check_clean(self, live_client, computed):
        result, _ = computed
        warnings = check_result_consistency(result)
        assert warnings == [], f"consistency warnings: {warnings}"
