"""
Live unit-fuzzing tests (bug-class prevention for F1).

F1 was: create_exchange hardcoded every exchange to Mass/kg, so a transport
flow (real reference property "Goods transport (mass*distance)", unit t*km)
silently had its amount reinterpreted in the wrong unit — a ~1000x error. This
file exercises the fix against a REAL openLCA database: for several flows whose
reference property is NOT Mass (transport, electricity/energy, land use), assert
create_exchange derives that flow's own unit rather than coercing to kg.

Requires:
  1. openLCA desktop app running with a database open (ideally with ecoinvent
     or another background dataset — flows not found are skipped, not failed).
  2. IPC server started (Tools -> Developer tools -> IPC server).

Run:
    pytest -m live tests/test_unit_fuzzing_live.py
"""
from __future__ import annotations

import os
import time
import pytest
import olca_schema as o
from openlca_ipc import OLCAClient


def _port() -> int:
    return int(os.environ.get("OLCA_IPC_PORT", "8080"))


def _unique(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000) % 100_000}"


@pytest.fixture(scope="module")
def live_client():
    try:
        client = OLCAClient(port=_port())
    except ConnectionError as exc:
        pytest.skip(f"openLCA IPC server not available on port {_port()}: {exc}")
    yield client


# (case name, candidate flow-name keywords to search for, forbidden unit name
# for a non-mass flow — 'kg' would indicate the F1 bug resurfaced)
LIVE_CASES = [
    ("transport", [["transport, freight, lorry"], ["transport, freight"], ["transport"]]),
    ("energy", [["electricity, high voltage"], ["electricity"], ["heat, district"]]),
    ("land_use", [["occupation, industrial area"], ["occupation"], ["transformation, to"]]),
]


@pytest.mark.live
class TestUnitFuzzingLive:

    @pytest.mark.parametrize(
        "case_name,keyword_sets", LIVE_CASES, ids=[c[0] for c in LIVE_CASES]
    )
    def test_create_exchange_derives_real_flow_unit(
        self, live_client, case_name, keyword_sets
    ):
        flow = None
        for kws in keyword_sets:
            hits = live_client.search.find_flows(kws, max_results=5)
            if hits:
                flow = hits[0]
                break
        if flow is None:
            pytest.skip(f"No {case_name} flow found in the active database")

        ex = live_client.data.create_exchange(flow, amount=1.0, is_input=True)

        assert ex.unit is not None, f"[{case_name}] {flow.name}: unit was not set"
        assert ex.flow_property is not None, (
            f"[{case_name}] {flow.name}: flow_property was not set"
        )
        assert ex.unit.name.lower() != "kg", (
            f"[{case_name}] {flow.name} was forced to kg "
            f"(F1 regression) — got unit={ex.unit.name!r}, "
            f"flow_property={ex.flow_property.name!r}"
        )

    def test_mass_flow_still_gets_kg(self, live_client):
        """Sanity check: an actual mass flow (e.g. tap water) is unaffected —
        the fix must not have broken the common case."""
        flow = None
        for kws in (["tap water"], ["water, completely softened"], ["steel"]):
            hits = live_client.search.find_flows(kws, max_results=5)
            if hits:
                flow = hits[0]
                break
        if flow is None:
            pytest.skip("No mass-reference flow found in the active database")

        ex = live_client.data.create_exchange(flow, amount=1.0, is_input=True)
        assert ex.flow_property.name == "Mass"
        assert ex.unit.name == "kg"

    def test_full_process_with_transport_exchange_correct_scale(self, live_client):
        """End-to-end: build a tiny process consuming a transport flow with
        formula '0.065*500/1000' and assert the STORED exchange keeps the
        correct t*km amount/unit — the exact scenario that was 1000x wrong."""
        hits = []
        for kws in (["transport, freight, lorry 16-32"], ["transport, freight, lorry"],
                    ["transport, freight"]):
            hits = live_client.search.find_flows(kws, max_results=3)
            if hits:
                break
        if not hits:
            pytest.skip("No lorry transport flow found in the active database")
        transport_flow = hits[0]

        out_flow = live_client.data.create_product_flow(_unique("fuzz_out"))
        ex_out = live_client.data.create_exchange(
            out_flow, amount=1.0, is_input=False, is_quantitative_reference=True
        )
        ex_transport = live_client.data.create_exchange(
            transport_flow, amount=0.0325, is_input=True, formula="0.065*500/1000"
        )
        process = live_client.data.create_process(
            _unique("fuzz_proc"), exchanges=[ex_out, ex_transport]
        )
        stored = next(e for e in process.exchanges if e.flow.id == transport_flow.id)
        assert stored.amount == pytest.approx(0.0325)
        assert stored.unit.name.lower() != "kg"
        assert stored.formula == "0.065*500/1000"

        live_client.client.delete(o.Ref(id=process.id, ref_type=o.RefType.Process))
        live_client.client.delete(o.Ref(id=out_flow.id, ref_type=o.RefType.Flow))
