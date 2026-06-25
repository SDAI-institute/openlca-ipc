# ============================================================================
# FILE: openlca_ipc/agent/summaries.py
# ============================================================================

"""
Compact, structured summaries for agent / MCP consumption.

Agents reason better over small, typed payloads than over large raw openLCA
schema objects. These dataclasses produce the compact JSON shape described in
``dev-actions/about_openlca-ipc.md`` (entity summaries and a result summary
with ``top_impacts`` and ``next_actions``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _ref_dict(ref: Any) -> Optional[Dict[str, Any]]:
    """Return a compact ``{id, name}`` dict for an olca_schema Ref-like object."""
    if ref is None:
        return None
    return {
        "id": getattr(ref, "id", None),
        "name": getattr(ref, "name", None),
    }


@dataclass
class EntitySummary:
    """Compact summary of a single openLCA entity (flow, process, method, ...)."""

    id: Optional[str]
    name: Optional[str]
    type: Optional[str] = None
    category: Optional[str] = None

    @classmethod
    def from_ref(cls, ref: Any, type_name: Optional[str] = None) -> "EntitySummary":
        """Build a summary from an olca_schema ``Ref`` (or any id/name object)."""
        return cls(
            id=getattr(ref, "id", None),
            name=getattr(ref, "name", None),
            type=type_name or getattr(ref, "ref_type", None) or type(ref).__name__,
            category=getattr(ref, "category", None),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "category": self.category,
        }

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class ResultSummary:
    """
    Compact summary of a calculation result for agent responses.

    Mirrors the JSON shape in the about-doc: identifiers plus the top impact
    categories and a list of suggested ``next_actions``.
    """

    result_id: Optional[str] = None
    database: Optional[str] = None
    product_system: Optional[Dict[str, Any]] = None
    functional_unit: Optional[Dict[str, Any]] = None
    impact_method: Optional[Dict[str, Any]] = None
    top_impacts: List[Dict[str, Any]] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    _DEFAULT_NEXT_ACTIONS = [
        "inspect_contribution_tree",
        "compare_scenario",
        "export_report",
    ]

    @classmethod
    def from_impacts(
        cls,
        impacts: List[Dict[str, Any]],
        *,
        result_id: Optional[str] = None,
        database: Optional[str] = None,
        product_system: Any = None,
        functional_unit: Optional[Dict[str, Any]] = None,
        impact_method: Any = None,
        top_n: int = 5,
        next_actions: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> "ResultSummary":
        """
        Build a ResultSummary from a list of impact dicts (as returned by
        ``ResultsAnalyzer.get_total_impacts``).

        ``product_system`` and ``impact_method`` may be passed as olca_schema
        Ref-like objects (compacted to ``{id, name}``) or as plain dicts.
        ``impacts`` are sorted by absolute amount and truncated to ``top_n``.
        """
        ranked = sorted(
            impacts, key=lambda i: abs(i.get("amount", 0.0) or 0.0), reverse=True
        )
        top = [
            {
                "category": i.get("name", ""),
                "amount": i.get("amount", 0.0),
                "unit": i.get("unit", ""),
            }
            for i in ranked[:top_n]
        ]

        def _maybe_ref(value: Any) -> Optional[Dict[str, Any]]:
            if value is None or isinstance(value, dict):
                return value
            return _ref_dict(value)

        return cls(
            result_id=result_id,
            database=database,
            product_system=_maybe_ref(product_system),
            functional_unit=functional_unit,
            impact_method=_maybe_ref(impact_method),
            top_impacts=top,
            next_actions=(
                list(next_actions)
                if next_actions is not None
                else list(cls._DEFAULT_NEXT_ACTIONS)
            ),
            warnings=list(warnings) if warnings else [],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "database": self.database,
            "product_system": self.product_system,
            "functional_unit": self.functional_unit,
            "impact_method": self.impact_method,
            "top_impacts": list(self.top_impacts),
            "next_actions": list(self.next_actions),
            "warnings": list(self.warnings),
        }

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
