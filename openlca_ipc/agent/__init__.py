# ============================================================================
# FILE: openlca_ipc/agent/__init__.py
# ============================================================================

"""
Agent-facing layer for openLCA IPC workflows.

Optional, additive helpers that make the library easier to drive from AI
agents and MCP servers:

- :mod:`~openlca_ipc.agent.summaries` — compact structured summaries
  (``EntitySummary``, ``ResultSummary``) with ``to_dict`` / ``to_json``.
- :mod:`~openlca_ipc.agent.reproducibility` — ``CalculationContext`` provenance.
- :mod:`~openlca_ipc.agent.errors` — recoverable structured errors (``OLCAError``).
- :mod:`~openlca_ipc.agent.health` — ``health_check`` readiness probe.

Nothing here changes the behaviour of the core managers; import what you need.
"""

from .errors import (
    OLCAError,
    ConnectionFailed,
    ImpactMethodNotFound,
    SystemNotFound,
    EntityNotFound,
    CalculationFailed,
    WriteBlocked,
)
from .summaries import EntitySummary, ResultSummary
from .reproducibility import CalculationContext
from .health import health_check

__all__ = [
    "OLCAError",
    "ConnectionFailed",
    "ImpactMethodNotFound",
    "SystemNotFound",
    "EntityNotFound",
    "CalculationFailed",
    "WriteBlocked",
    "EntitySummary",
    "ResultSummary",
    "CalculationContext",
    "health_check",
]
