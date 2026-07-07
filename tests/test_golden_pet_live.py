"""
PET/PC regression baseline (WS3b).

Locks in OUR OWN verified post-fix results for the tutorial's PET/PC chain
(`fixtures/pet_golden.json`) as a regression guard: if a future change to
`openlca_ipc` or the modelling helper shifts these numbers beyond tolerance,
this test catches it immediately. The baseline is intentionally NOT the
tutorial PDF's published numbers -- those differ by a known, root-caused
~0.78x background-dataset factor (see `openlca-ipc case studies/
case1-findings.md`, "Residual ~0.78x") that has nothing to do with the
library/MCP being tested here. Comparing against our own prior verified run
isolates "did WE change something" from "did ecoinvent's background data
change" or "does the tutorial's exact PDF vintage match this database".

Requires:
  1. openLCA desktop app running with the ecoinvent 3.10 Cutoff Unit-Processes
     database open (the specific background flows/providers this test
     resolves are ecoinvent-specific; the test is skipped if not found).
  2. IPC server started (Tools -> Developer tools -> IPC server).

Run:
    pytest -m live tests/test_golden_pet_live.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import olca_schema as o
import olca_ipc as ipc
from openlca_ipc import SearchUtils, CalculationManager, ResultsAnalyzer

from tests.fixtures.pet_system import build_pet_pc_chain, cleanup_pet_pc_chain

BASELINE = json.loads((Path(__file__).parent / "fixtures" / "pet_golden.json").read_text())


def _port() -> int:
    return int(os.environ.get("OLCA_IPC_PORT", "8080"))


@pytest.fixture(scope="module")
def live_client():
    client = ipc.Client(_port())
    try:
        next(iter(client.get_descriptors(o.Flow)), None)  # fail fast if unreachable
    except Exception as exc:
        pytest.skip(f"openLCA IPC server not available on port {_port()}: {exc}")
    return client


@pytest.fixture(scope="module")
def method(live_client):
    search = SearchUtils(live_client)
    m = search.find_impact_method([BASELINE["method"]])
    if m is None:
        pytest.skip(f"{BASELINE['method']!r} not found in the active database")
    return m


@pytest.fixture(scope="module")
def chain(live_client, method):
    """Build the PET/PC chain once for this module; require the ecoinvent
    background flows it depends on, else skip the whole module."""
    try:
        built = build_pet_pc_chain(live_client, method, tag="PETGOLD")
    except Exception as exc:
        pytest.skip(f"Could not build PET/PC chain (ecoinvent flows missing?): {exc}")
    try:
        yield built
    finally:
        cleanup_pet_pc_chain(live_client, built)


def _totals(live_client, method, system_ref) -> dict:
    calc = CalculationManager(live_client)
    results = ResultsAnalyzer(live_client)
    result = calc.simple_calculation(system_ref, method, BASELINE["amount"])
    try:
        return {i["name"]: i["amount"] for i in results.get_total_impacts(result)}
    finally:
        result.dispose()


@pytest.mark.live
class TestPetGoldenRegression:

    @pytest.mark.parametrize("which", ["pet", "pc"])
    def test_matches_baseline(self, live_client, method, chain, which):
        system_ref = chain.pet_system if which == "pet" else chain.pc_system
        actual = _totals(live_client, method, system_ref)
        expected = BASELINE["impacts"][which]
        rel_tol = BASELINE["rel_tol"]
        abs_tol = BASELINE["abs_tol"]

        # A category passes if EITHER the relative difference is within
        # tolerance OR the absolute difference is negligible -- categories
        # near zero (e.g. land-use for a mostly-transport chain) carry more
        # relative float noise than their magnitude warrants.
        failures = []
        for category, expected_value in expected.items():
            got = actual.get(category)
            if got is None:
                failures.append(f"{category}: missing from result")
                continue
            abs_diff = abs(got - expected_value)
            rel = abs_diff / max(abs(expected_value), 1e-12)
            if rel > rel_tol and abs_diff > abs_tol:
                failures.append(
                    f"{category}: expected {expected_value:.6g}, got {got:.6g} "
                    f"({rel * 100:.2f}% > {rel_tol * 100:.1f}% tolerance, "
                    f"abs diff {abs_diff:.3g} > {abs_tol:.3g})"
                )
        assert not failures, (
            f"{which.upper()} regressed vs pet_golden.json baseline:\n  "
            + "\n  ".join(failures)
        )
