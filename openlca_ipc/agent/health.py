# ============================================================================
# FILE: openlca_ipc/agent/health.py
# ============================================================================

"""
Health / readiness check for the openLCA IPC connection.

Backs a future ``openlca_health`` MCP tool: a single call that tells an agent
whether the server is reachable, which port it is on, and how much data the
active database holds.
"""

from __future__ import annotations

from typing import Any, Dict

import olca_schema as o


_ENTITY_TYPES = [
    ("processes", o.Process),
    ("flows", o.Flow),
    ("impact_methods", o.ImpactMethod),
    ("product_systems", o.ProductSystem),
]


def health_check(client: Any, *, count_entities: bool = True) -> Dict[str, Any]:
    """
    Probe the openLCA IPC connection and return a structured status report.

    Args:
        client: An :class:`~openlca_ipc.client.OLCAClient` or a raw
            ``olca_ipc.Client``. (An ``OLCAClient`` is unwrapped automatically.)
        count_entities: If True (default), include entity counts per type.
            Set False to skip the (potentially slow) descriptor scans.

    Returns:
        Dict with keys: ``connected`` (bool), ``server_port``, ``counts``
        (dict per entity type), and ``errors`` (list of strings).
    """
    raw = getattr(client, "client", client)
    report: Dict[str, Any] = {
        "connected": False,
        "server_port": getattr(client, "port", None),
        "counts": {},
        "errors": [],
    }

    try:
        # "Mass" is a reference flow property present in every openLCA database.
        mass = raw.get(o.FlowProperty, name="Mass")
        report["connected"] = mass is not None
    except Exception as e:  # noqa: BLE001 - report, don't raise
        report["errors"].append(f"connection: {e}")
        return report

    if count_entities and report["connected"]:
        for label, entity_type in _ENTITY_TYPES:
            try:
                report["counts"][label] = len(raw.get_descriptors(entity_type))
            except Exception as e:  # noqa: BLE001
                report["errors"].append(f"{label}: {e}")

    return report
