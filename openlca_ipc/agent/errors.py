# ============================================================================
# FILE: openlca_ipc/agent/errors.py
# ============================================================================

"""
Recoverable, structured errors for agent-facing workflows.

These errors carry a machine-readable ``error_code`` and a list of
``suggested_next_actions`` so a calling agent (or MCP tool) can decide what to
do next instead of parsing a free-text message. Every error serialises to the
envelope shape documented in ``dev-actions/about_openlca-ipc.md``::

    {
      "is_error": true,
      "error_code": "IMPACT_METHOD_NOT_FOUND",
      "message": "No impact method matched 'EF 3.1'.",
      "recoverable": true,
      "suggested_next_actions": ["search_impact_methods"]
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class OLCAError(Exception):
    """
    Base class for structured, agent-friendly openLCA errors.

    Attributes:
        error_code: Stable, machine-readable code (e.g. ``"IMPACT_METHOD_NOT_FOUND"``).
        message: Human-readable description.
        recoverable: Whether the caller can plausibly recover (default True).
        suggested_next_actions: Ordered list of action hints for the caller.
    """

    #: Default code used when a subclass / caller does not supply one.
    default_code: str = "OLCA_ERROR"
    #: Default next-action hints for this error class.
    default_actions: List[str] = []

    def __init__(
        self,
        error_code: Optional[str] = None,
        message: str = "",
        *,
        recoverable: bool = True,
        suggested_next_actions: Optional[List[str]] = None,
    ):
        self.error_code = error_code or self.default_code
        self.message = message or self.__class__.__name__
        self.recoverable = recoverable
        self.suggested_next_actions = (
            list(suggested_next_actions)
            if suggested_next_actions is not None
            else list(self.default_actions)
        )
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to the agent error envelope."""
        return {
            "is_error": True,
            "error_code": self.error_code,
            "message": self.message,
            "recoverable": self.recoverable,
            "suggested_next_actions": list(self.suggested_next_actions),
        }


class ConnectionFailed(OLCAError):
    """Could not reach the openLCA IPC server."""

    default_code = "CONNECTION_FAILED"
    default_actions = ["check_ipc_server_running", "verify_port"]


class ImpactMethodNotFound(OLCAError):
    """No impact method matched the requested name/keywords."""

    default_code = "IMPACT_METHOD_NOT_FOUND"
    default_actions = ["search_impact_methods"]


class SystemNotFound(OLCAError):
    """No product system matched the request."""

    default_code = "SYSTEM_NOT_FOUND"
    default_actions = ["search_product_systems", "create_product_system"]


class EntityNotFound(OLCAError):
    """A requested entity (flow, process, ...) could not be found."""

    default_code = "ENTITY_NOT_FOUND"
    default_actions = ["search_entities"]


class CalculationFailed(OLCAError):
    """A calculation could not be completed."""

    default_code = "CALCULATION_FAILED"
    default_actions = ["verify_product_system", "verify_impact_method"]


class WriteBlocked(OLCAError):
    """A write was attempted while the client is in read-only (safe) mode."""

    default_code = "WRITE_BLOCKED"
    default_actions = ["disable_read_only_mode"]

    def __init__(
        self,
        message: str = "Write blocked: client is in read-only mode.",
        *,
        operation: Optional[str] = None,
    ):
        if operation:
            message = f"Write blocked: '{operation}' is not allowed in read-only mode."
        super().__init__(self.default_code, message, recoverable=True)
        self.operation = operation
