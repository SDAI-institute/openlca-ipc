"""
Live provider-invariant tests (bug-class prevention for F3).

F3 was: find_providers returned bare {id, name, category} with no geography,
so several providers shared an IDENTICAL name string but different ids
(differing only by location — e.g. RER vs RoW vs CA-QC). Left to blind
auto-selection, the MCP picked a Canada-Quebec PET-granulate provider and a
GLO tap-water market instead of the tutorial's required RER datasets, because
there was no way to tell them apart. The `o.Ref` objects returned by
find_providers already carry a `location` field; this file asserts that field
is actually present and actually disambiguates same-named providers, against a
REAL openLCA database.

Requires:
  1. openLCA desktop app running with a database open (ideally with a
     background dataset like ecoinvent — flows not found are skipped).
  2. IPC server started (Tools -> Developer tools -> IPC server).

Run:
    pytest -m live tests/test_search_live.py
"""
from __future__ import annotations

import os
import pytest
from openlca_ipc import OLCAClient


def _port() -> int:
    return int(os.environ.get("OLCA_IPC_PORT", "8080"))


@pytest.fixture(scope="module")
def live_client():
    try:
        client = OLCAClient(port=_port())
    except ConnectionError as exc:
        pytest.skip(f"openLCA IPC server not available on port {_port()}: {exc}")
    yield client


# Flows likely to have multiple geography-differentiated providers in a
# background dataset like ecoinvent.
FLOW_KEYWORDS = [
    ["transport, freight, lorry"],
    ["tap water"],
    ["polyethylene terephthalate, granulate, bottle grade"],
    ["electricity, high voltage"],
    ["polyethylene, high density, granulate"],
]


def _first_flow_with_providers(live_client):
    """Return (flow, providers) for the first keyword set with >=1 provider."""
    for kws in FLOW_KEYWORDS:
        flows = live_client.search.find_flows(kws, max_results=3)
        if not flows:
            continue
        providers = live_client.search.find_providers(flows[0])
        if providers:
            return flows[0], providers
    return None, []


@pytest.mark.live
class TestProviderInvariantsLive:

    def test_providers_carry_location(self, live_client):
        """Every provider returned must expose a location -- otherwise
        geography-aware selection (the tutorial's core "pick RER" step) is
        impossible through the library/MCP, as it was pre-fix."""
        flow, providers = _first_flow_with_providers(live_client)
        if flow is None:
            pytest.skip("No candidate flow with providers found in the active database")

        missing = [p for p in providers if not getattr(p, "location", None)]
        assert not missing, (
            f"{len(missing)}/{len(providers)} providers for {flow.name!r} have no "
            f"location: {[p.name for p in missing][:3]}"
        )

    def test_same_named_providers_are_distinguished_by_location(self, live_client):
        """The literal F3 failure mode: two providers sharing an IDENTICAL
        name string but different ids, with no location to tell them apart."""
        checked_any = False
        for kws in FLOW_KEYWORDS:
            flows = live_client.search.find_flows(kws, max_results=3)
            if not flows:
                continue
            providers = live_client.search.find_providers(flows[0])
            if len(providers) < 2:
                continue

            by_name: dict[str, list] = {}
            for p in providers:
                by_name.setdefault(p.name, []).append(p)

            for name, group in by_name.items():
                if len(group) < 2:
                    continue
                checked_any = True
                locations = {getattr(p, "location", None) for p in group}
                assert None not in locations, (
                    f"{len(group)} providers named {name!r} for flow "
                    f"{flows[0].name!r} include one with no location -- cannot "
                    f"be disambiguated: ids {[p.id for p in group]}"
                )
                assert len(locations) == len(group), (
                    f"{len(group)} providers named {name!r} for flow "
                    f"{flows[0].name!r} share locations {locations} -- "
                    f"location does not disambiguate them: "
                    f"{[(p.id, p.location) for p in group]}"
                )

        if not checked_any:
            pytest.skip(
                "No flow with >=2 same-named providers found in the active database"
            )
