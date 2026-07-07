"""
Live smoke test for openlca-ipc against a running openLCA IPC server.

Run this on the machine where openLCA is running with the IPC server started
(openLCA: Tools -> Developer tools -> IPC server). It connects to the server,
exercises the main client paths, and reports what works against your database.

Usage:
    python examples/live_smoke_test.py            # uses port 8080
    python examples/live_smoke_test.py --port 8080
    python examples/live_smoke_test.py --calc     # also run a calculation

Exit code is 0 if the connection works, 1 otherwise. Individual feature
checks degrade gracefully (SKIP) when the database lacks the needed data,
so an empty/partial database won't fail the run.
"""
from __future__ import annotations

import argparse
import sys

import olca_schema as o
from openlca_ipc import OLCAClient


# --- tiny console helpers ---------------------------------------------------
def _ok(msg: str) -> None:
    print(f"  [PASS] {msg}")


def _skip(msg: str) -> None:
    print(f"  [SKIP] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _section(title: str) -> None:
    print(f"\n=== {title} ===")


def _is_connection_error(exc: Exception) -> bool:
    """Heuristic: does this exception mean the server isn't reachable?"""
    text = f"{type(exc).__name__}: {exc}".lower()
    needles = ("connection refused", "refused", "max retries", "10061",
               "failed to establish", "newconnectionerror", "connectionerror")
    return any(n in text for n in needles)


def _print_server_hint(port: int) -> None:
    print(
        f"\nNo IPC server is listening on port {port}. In openLCA:\n"
        "  1. Open (activate) a database.\n"
        "  2. Start the IPC server for it and confirm the port number.\n"
        f"  3. From a terminal, verify it is listening:\n"
        f"       netstat -ano | findstr :{port}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="openlca-ipc live smoke test")
    parser.add_argument("--port", type=int, default=8080, help="IPC server port")
    parser.add_argument("--calc", action="store_true",
                        help="also attempt a full product-system calculation")
    args = parser.parse_args()

    print(f"openlca-ipc live smoke test -> port {args.port}")

    # --- Connection ---------------------------------------------------------
    _section("Connection")
    try:
        client = OLCAClient(port=args.port)
    except ConnectionError as e:
        _fail(f"Could not connect: {e}")
        _print_server_hint(args.port)
        return 1

    # The openLCA IPC client connects lazily, so OLCAClient(...) succeeds even
    # when nothing is listening. Probe with a real request and classify the
    # failure: server unreachable vs. reachable-but-no-database-open.
    try:
        mass = client.client.get(o.FlowProperty, name="Mass")
    except Exception as e:  # noqa: BLE001 - diagnostic tool
        if _is_connection_error(e):
            _fail(f"No IPC server reachable on port {args.port}")
            _print_server_hint(args.port)
        else:
            _fail(f"Request to the server failed: {e}")
        return 1

    if mass is not None:
        _ok("Server reachable and 'Mass' flow property resolved")
    else:
        _fail("Server reachable, but no 'Mass' property found - "
              "open a database in openLCA before running.")
        return 1

    # --- Search -------------------------------------------------------------
    _section("Search")
    flow = None
    for kws in (["steel"], ["water"], ["electricity"], ["carbon"]):
        try:
            found = client.search.find_flows(kws, max_results=3)
        except Exception as e:  # noqa: BLE001 - reporting tool
            _fail(f"find_flows({kws}) raised: {e}")
            found = []
        if found:
            flow = found[0]
            _ok(f"find_flows({kws}) -> {len(found)} hit(s); first: {flow.name!r}")
            break
    if flow is None:
        _skip("No common flows found - database may be empty or specialised")

    try:
        procs = client.search.find_processes(["production"], max_results=3)
        if procs:
            _ok(f"find_processes(['production']) -> {len(procs)} hit(s); "
                f"first: {procs[0].name!r}")
        else:
            _skip("find_processes(['production']) -> no hits")
    except Exception as e:  # noqa: BLE001
        _fail(f"find_processes raised: {e}")

    method = None
    for kws in (["TRACI"], ["ReCiPe"], ["CML"], ["EF"], ["IMPACT"]):
        try:
            method = client.search.find_impact_method(kws)
        except Exception as e:  # noqa: BLE001
            _fail(f"find_impact_method({kws}) raised: {e}")
            method = None
        if method is not None:
            _ok(f"find_impact_method({kws}) -> {method.name!r}")
            break
    if method is None:
        _skip("No common impact method found in this database")

    # --- Providers ----------------------------------------------------------
    _section("Providers")
    if flow is not None:
        try:
            providers = client.search.find_providers(flow)
            if providers:
                _ok(f"find_providers({flow.name!r}) -> {len(providers)} provider(s)")
            else:
                _skip(f"No providers linked for {flow.name!r}")
        except Exception as e:  # noqa: BLE001
            _fail(f"find_providers raised: {e}")
    else:
        _skip("No flow available to look up providers")

    # --- Optional calculation ----------------------------------------------
    if args.calc:
        _section("Calculation")
        _run_calculation(client, method)
    else:
        _section("Calculation")
        _skip("Skipped (pass --calc to attempt a full calculation)")

    print("\nSmoke test complete: connection is healthy.")
    return 0


def _run_calculation(client: OLCAClient, method) -> None:
    """Build a product system from a process and calculate it."""
    try:
        systems = client.client.get_descriptors(o.ProductSystem)
    except Exception as e:  # noqa: BLE001
        _fail(f"Listing product systems raised: {e}")
        return

    system_ref = systems[0] if systems else None

    if system_ref is None:
        # Try to build a product system from any process.
        try:
            procs = client.client.get_descriptors(o.Process)
        except Exception as e:  # noqa: BLE001
            _fail(f"Listing processes raised: {e}")
            return
        if not procs:
            _skip("No product systems or processes to calculate")
            return
        proc = client.client.get(o.Process, procs[0].id)
        system_ref = client.systems.create_product_system(proc)
        if system_ref is None:
            _skip("Could not auto-build a product system")
            return
        _ok(f"Built product system from process {proc.name!r}")
    else:
        _ok(f"Using existing product system {system_ref.name!r}")

    try:
        result = client.calculate.simple_calculation(
            system=system_ref, impact_method=method, amount=1.0
        )
    except Exception as e:  # noqa: BLE001
        _fail(f"Calculation raised: {e}")
        return

    try:
        impacts = client.results.get_total_impacts(result)
        if impacts:
            _ok(f"Calculation produced {len(impacts)} impact categories")
            for imp in impacts[:5]:
                print(f"        {imp['name']}: {imp['amount']:.4e} {imp['unit']}")
        else:
            _skip("Calculation ran but returned no impacts "
                  "(no impact method, or inventory-only)")
    finally:
        # Always release native result resources.
        try:
            result.dispose()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    sys.exit(main())
