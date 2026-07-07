# ============================================================================
# FILE: openlca_ipc/agent/reproducibility.py
# ============================================================================

"""
Reproducibility metadata for openLCA calculations.

Captures the context needed to understand how a result was produced after the
fact — database identity, library/IPC versions, product system, functional
unit, impact method, calculation settings, a timestamp, and a generated
``result_id``. Attach ``CalculationContext.to_dict()`` to exported artifacts so
results remain auditable when passed between agents or written to reports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _version(pkg: str) -> Optional[str]:
    """Best-effort version lookup for an installed package."""
    try:
        from importlib.metadata import version, PackageNotFoundError
        try:
            return version(pkg)
        except PackageNotFoundError:
            return None
    except Exception:
        return None


def _ref_dict(ref: Any) -> Optional[Dict[str, Any]]:
    if ref is None:
        return None
    if isinstance(ref, dict):
        return ref
    return {"id": getattr(ref, "id", None), "name": getattr(ref, "name", None)}


@dataclass
class CalculationContext:
    """
    Provenance record for a single calculation.

    Use :meth:`capture` to auto-fill versions, timestamp, and ``result_id``.
    """

    result_id: str
    timestamp: str
    package_version: Optional[str] = None
    olca_ipc_version: Optional[str] = None
    olca_schema_version: Optional[str] = None
    server_port: Optional[int] = None
    database: Optional[str] = None
    product_system: Optional[Dict[str, Any]] = None
    reference_process: Optional[Dict[str, Any]] = None
    reference_flow: Optional[Dict[str, Any]] = None
    functional_unit: Optional[Dict[str, Any]] = None
    impact_method: Optional[Dict[str, Any]] = None
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def capture(
        cls,
        *,
        database: Optional[str] = None,
        server_port: Optional[int] = None,
        product_system: Any = None,
        reference_process: Any = None,
        reference_flow: Any = None,
        functional_unit: Optional[Dict[str, Any]] = None,
        impact_method: Any = None,
        settings: Optional[Dict[str, Any]] = None,
        result_id: Optional[str] = None,
    ) -> "CalculationContext":
        """Build a context, auto-filling versions, timestamp, and result id."""
        return cls(
            result_id=result_id or f"res_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            package_version=_version("openlca-ipc"),
            olca_ipc_version=_version("olca-ipc"),
            olca_schema_version=_version("olca-schema"),
            server_port=server_port,
            database=database,
            product_system=_ref_dict(product_system),
            reference_process=_ref_dict(reference_process),
            reference_flow=_ref_dict(reference_flow),
            functional_unit=functional_unit,
            impact_method=_ref_dict(impact_method),
            settings=dict(settings) if settings else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "timestamp": self.timestamp,
            "package_version": self.package_version,
            "olca_ipc_version": self.olca_ipc_version,
            "olca_schema_version": self.olca_schema_version,
            "server_port": self.server_port,
            "database": self.database,
            "product_system": self.product_system,
            "reference_process": self.reference_process,
            "reference_flow": self.reference_flow,
            "functional_unit": self.functional_unit,
            "impact_method": self.impact_method,
            "settings": dict(self.settings),
        }
