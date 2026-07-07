"""
Golden-value regression tests against a SYNTHETIC, license-free system.

Unlike the Case-1 PET/PC tutorial reproduction (paid ecoinvent 3.10 DB, subject
to background-dataset revision drift — see `openlca-ipc case studies/
case1-findings.md`), this system is built entirely from user-defined entities
(one elementary flow, one impact method/category, two product flows, a 2-level
process chain) with a hand-derivable answer. It runs against ANY openLCA
database and doubles as an independent cross-check (WS4a): the expected value
is computed by hand, not by another modelling tool's opinion.

See `tests/fixtures/golden_system.py` for the model and
`openlca-ipc case studies/case2-golden-handcalc.md` for the full derivation.
Expected total impact = 6.5 kg CO2e for 1 kg "Golden Product".

Requires:
  1. openLCA desktop app running with a database open (any database — no
     ecoinvent or other license needed).
  2. IPC server started (Tools -> Developer tools -> IPC server).

Run:
    pytest -m live tests/test_golden_live.py
"""
from __future__ import annotations

import os
import pytest
from openlca_ipc import OLCAClient

from tests.fixtures.golden_system import build_golden_system, cleanup_golden_system


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
def golden(live_client):
    """Build the golden system once for this module; tear it down after."""
    g = build_golden_system(live_client)
    try:
        yield g
    finally:
        cleanup_golden_system(live_client, g)


def _golden_amount(live_client, golden, amount: float = 1.0) -> float:
    result = live_client.calculate.simple_calculation(golden.system_ref, golden.method, amount)
    try:
        impacts = {i["name"]: i["amount"] for i in live_client.results.get_total_impacts(result)}
    finally:
        result.dispose()
    return impacts[golden.method.impact_categories[0].name]


@pytest.mark.live
class TestGoldenSystemHandCalc:
    """WS3a / WS4a: the synthetic system reproduces its hand-derived answer."""

    def test_matches_hand_calculation(self, live_client, golden):
        amount = _golden_amount(live_client, golden)
        assert amount == pytest.approx(golden.expected_impact, rel=1e-9)

    def test_scales_linearly_with_functional_unit(self, live_client, golden):
        """2 kg of Golden Product should give exactly 2x the impact (no
        allocation/cutoff in this model — pure linear scaling)."""
        amount = _golden_amount(live_client, golden, amount=2.0)
        assert amount == pytest.approx(2 * golden.expected_impact, rel=1e-9)


@pytest.mark.live
class TestGoldenSystemDeterminism:
    """WS3c: repeated calculations of the identical system must be bit-identical
    (openLCA's LCA solve is deterministic; no Monte Carlo / sampling involved
    in a simple_calculation)."""

    def test_repeated_calculations_are_identical(self, live_client, golden):
        K = 5
        totals = [_golden_amount(live_client, golden) for _ in range(K)]
        spread = max(totals) - min(totals)
        assert spread == 0.0, f"Non-deterministic result across {K} runs: {totals}"
        assert all(t == pytest.approx(golden.expected_impact, rel=1e-9) for t in totals)
