# Agent Layer API Reference (`openlca_ipc.agent`)

The `openlca_ipc.agent` subpackage provides compact structured outputs, reproducibility
metadata, recoverable error types, and a health probe. It is designed for AI agent and
MCP server use-cases where you need predictable JSON payloads rather than raw
openLCA schema objects.

Nothing in this subpackage changes the behaviour of the core managers — import only
what you need.

**Full usage guide:** [documentation/agent-usage.md](../agent-usage.md)

---

## `health_check`

```python
from openlca_ipc import health_check

health_check(client, *, count_entities: bool = True) -> dict
```

Probes whether the IPC server is reachable and returns entity counts for the active
database. Accepts either `OLCAClient` or a raw `olca_ipc.Client`.

**Returns:**
```json
{
  "connected": true,
  "server_port": 8080,
  "counts": {
    "processes": 1234,
    "flows": 5678,
    "impact_methods": 12,
    "product_systems": 7
  },
  "errors": []
}
```

Pass `count_entities=False` to skip descriptor scans (faster, but no counts).

---

## `ResultSummary`

Compact, JSON-ready summary of a calculation result.

```python
from openlca_ipc import ResultSummary

summary = ResultSummary.from_impacts(
    impacts,                        # list from ResultsAnalyzer.get_total_impacts()
    *,
    result_id=None,                 # str — generated UUID if omitted
    database=None,                  # str
    product_system=None,            # o.Ref or dict
    functional_unit=None,           # dict: {amount, unit, description}
    impact_method=None,             # o.Ref or dict
    top_n=5,                        # how many categories to include
    warnings=None,                  # list[str] from check_result_consistency()
)
```

**Methods:**
- `.to_dict() -> dict` — plain-Python dict (JSON-serialisable).
- `.to_json(*, indent=2) -> str` — JSON string.

**Shape:**
```json
{
  "result_id": "...",
  "database": "...",
  "product_system": {"id": "...", "name": "..."},
  "functional_unit": {"amount": 1, "unit": "kg"},
  "impact_method": {"id": "...", "name": "EF 3.1"},
  "top_impacts": [
    {"category": "Climate change", "amount": 2.84, "unit": "kg CO2 eq"}
  ],
  "next_actions": ["inspect_contribution_tree", "compare_scenario", "export_report"],
  "warnings": []
}
```

---

## `EntitySummary`

Compact summary for a single openLCA entity (flow, process, method, etc.).

```python
from openlca_ipc import EntitySummary

summary = EntitySummary.from_ref(ref, type_name=None)
```

**Methods:**
- `.to_dict() -> dict` — `{id, name, type, category}`.

---

## `CalculationContext`

Captures everything needed to reproduce or audit a calculation result.

```python
from openlca_ipc import CalculationContext

context = CalculationContext.capture(
    *,
    database=None,
    server_port=None,
    product_system=None,      # o.Ref or dict
    reference_process=None,   # o.Ref or dict
    impact_method=None,       # o.Ref or dict
    functional_unit=None,     # dict
    settings=None,            # dict — e.g. {"allocation": "PHYSICAL"}
)
```

Auto-filled fields: `result_id` (UUID), `timestamp` (ISO-8601), `package_version`,
`olca_ipc_version`, `olca_schema_version`.

**Methods:**
- `.to_dict() -> dict` — embed in exported artifacts to keep results auditable.

---

## Error classes

All errors derive from `OLCAError` and serialise to a recoverable envelope.

```python
from openlca_ipc.agent import (
    OLCAError,
    ConnectionFailed,
    ImpactMethodNotFound,
    SystemNotFound,
    EntityNotFound,
    CalculationFailed,
    WriteBlocked,
)
```

### `OLCAError`

Base class. All subclasses inherit `.to_dict()`:

```json
{
  "is_error": true,
  "error_code": "...",
  "message": "...",
  "recoverable": true,
  "suggested_next_actions": ["..."]
}
```

### Subclasses

| Class | `error_code` | `recoverable` | Suggested actions |
|-------|-------------|---------------|-------------------|
| `ConnectionFailed` | `CONNECTION_FAILED` | `false` | `check_ipc_server_running`, `verify_port` |
| `ImpactMethodNotFound` | `IMPACT_METHOD_NOT_FOUND` | `true` | `search_impact_methods` |
| `SystemNotFound` | `SYSTEM_NOT_FOUND` | `true` | `search_product_systems`, `create_product_system` |
| `EntityNotFound` | `ENTITY_NOT_FOUND` | `true` | `search_entities` |
| `CalculationFailed` | `CALCULATION_FAILED` | `true` | `verify_product_system`, `verify_impact_method` |
| `WriteBlocked` | `WRITE_BLOCKED` | `true` | `disable_read_only_mode` |

`WriteBlocked` also exposes an `operation` attribute naming the blocked method.

---

## Read-only safe mode

`OLCAClient(read_only=True)` wraps the underlying IPC client in `_ReadOnlyGuard`.
All write methods (`put`, `put_all`, `delete`, `delete_all`, `put_source_file`,
`create_product_system`) raise `WriteBlocked` before reaching the server. Reads,
searches, and calculations are unaffected.

```python
from openlca_ipc import OLCAClient
from openlca_ipc.agent import WriteBlocked

with OLCAClient(port=8080, read_only=True) as client:
    impacts = client.results.get_total_impacts(result)   # OK
    try:
        client.data.create_product_flow("test")          # raises WriteBlocked
    except WriteBlocked as e:
        print(e.to_dict())
```

---

## `check_result_consistency`

In `openlca_ipc.diagnostics` (not in `agent/`, but designed for agent pipelines):

```python
from openlca_ipc import check_result_consistency

warnings = check_result_consistency(result, *, rel_tol=1e-3, abs_tol=1e-12)
# -> list[str]   empty = all checks passed
```

Verifies that per-process contributions sum to each category total within tolerance.
Pass the result directly into `ResultSummary.from_impacts(..., warnings=warnings)`.

---

## See Also

- [Agent usage guide](../agent-usage.md) — complete MCP builder walkthrough
- [OLCAClient](client.md) — connection and safe mode setup
- [ResultsAnalyzer](results.md) — the result methods that feed `ResultSummary`
