# Agent & MCP Usage Guide

`openlca-ipc` ships an optional **agent layer** (`openlca_ipc.agent`) that makes
the library easy to drive from AI agents and MCP servers. It provides compact
structured responses, reproducibility metadata, recoverable structured errors,
a health probe, and a read-only safe mode.

Nothing here changes the behaviour of the core managers — import what you need.

---

## Why a separate layer?

Agents reason better over small, typed payloads than over large raw openLCA
schema objects. The agent layer returns compact JSON-ready dicts with stable
identifiers and suggested next actions, so an LLM or MCP tool can act on a
result without parsing full entity graphs.

```
AI agent / MCP server
        ↓  (compact JSON: summaries, errors, context)
openlca_ipc.agent
        ↓  (rich Python objects)
openlca_ipc managers  →  olca_ipc / olca_schema  →  openLCA database
```

---

## Health check

A single call that tells an agent whether the server is reachable and how much
data the active database holds. Backs an `openlca_health` MCP tool.

```python
from openlca_ipc import OLCAClient, health_check

with OLCAClient(port=8080) as client:
    print(health_check(client))
# {'connected': True, 'server_port': 8080,
#  'counts': {'processes': 1234, 'flows': 5678,
#             'impact_methods': 12, 'product_systems': 7},
#  'errors': []}
```

`health_check` accepts either an `OLCAClient` or a raw `olca_ipc.Client`. Pass
`count_entities=False` to skip the (potentially slow) descriptor scans.

---

## Structured result summaries

`ResultSummary` produces the compact JSON shape an agent can consume directly.

```python
from openlca_ipc import OLCAClient, ResultSummary

with OLCAClient(port=8080) as client:
    result = client.calculate.simple_calculation(system, method)
    try:
        impacts = client.results.get_total_impacts(result)
        summary = ResultSummary.from_impacts(
            impacts,
            result_id="res_001",
            database="example_database",
            product_system=system,     # Ref → compacted to {id, name}
            impact_method=method,      # Ref or dict
            functional_unit={"amount": 1, "unit": "L", "description": "1 L bottle"},
            top_n=5,
        )
        print(summary.to_json())
    finally:
        result.dispose()
```

```json
{
  "result_id": "res_001",
  "database": "example_database",
  "product_system": {"id": "...", "name": "PET bottle system"},
  "functional_unit": {"amount": 1, "unit": "L", "description": "1 L bottle"},
  "impact_method": {"id": "...", "name": "EF 3.1"},
  "top_impacts": [
    {"category": "Climate change", "amount": 2.84, "unit": "kg CO2 eq"}
  ],
  "next_actions": ["inspect_contribution_tree", "compare_scenario", "export_report"],
  "warnings": []
}
```

`EntitySummary` does the same for individual entities:

```python
from openlca_ipc import EntitySummary

flow = client.search.find_flow(['steel'])
print(EntitySummary.from_ref(flow, type_name="Flow").to_dict())
# {'id': '...', 'name': 'steel, ...', 'type': 'Flow', 'category': None}
```

---

## Reproducibility metadata

`CalculationContext` captures everything needed to understand how a result was
produced — database, library/IPC versions, product system, functional unit,
impact method, settings, an ISO-8601 timestamp, and a generated `result_id`.
Attach `to_dict()` to exported artifacts so results stay auditable.

```python
from openlca_ipc import CalculationContext

context = CalculationContext.capture(
    database="example_database",
    server_port=8080,
    product_system=system,
    reference_process=process,
    impact_method=method,
    functional_unit={"amount": 1, "unit": "L"},
    settings={"allocation": "PHYSICAL"},
)
artifact = {"context": context.to_dict(), "summary": summary.to_dict()}
```

Versions (`package_version`, `olca_ipc_version`, `olca_schema_version`),
`timestamp`, and `result_id` are filled in automatically.

---

## Recoverable structured errors

All agent errors derive from `OLCAError` and serialise to a recoverable
envelope an agent can branch on:

```python
from openlca_ipc.agent import (
    OLCAError, ConnectionFailed, ImpactMethodNotFound,
    SystemNotFound, EntityNotFound, CalculationFailed, WriteBlocked,
)

err = ImpactMethodNotFound(message="No impact method matched 'EF 3.1'.")
print(err.to_dict())
```

```json
{
  "is_error": true,
  "error_code": "IMPACT_METHOD_NOT_FOUND",
  "message": "No impact method matched 'EF 3.1'.",
  "recoverable": true,
  "suggested_next_actions": ["search_impact_methods"]
}
```

| Error class            | `error_code`              | Typical next actions                         |
| ---------------------- | ------------------------- | -------------------------------------------- |
| `ConnectionFailed`     | `CONNECTION_FAILED`       | `check_ipc_server_running`, `verify_port`    |
| `ImpactMethodNotFound` | `IMPACT_METHOD_NOT_FOUND` | `search_impact_methods`                      |
| `SystemNotFound`       | `SYSTEM_NOT_FOUND`        | `search_product_systems`, `create_product_system` |
| `EntityNotFound`       | `ENTITY_NOT_FOUND`        | `search_entities`                            |
| `CalculationFailed`    | `CALCULATION_FAILED`      | `verify_product_system`, `verify_impact_method` |
| `WriteBlocked`         | `WRITE_BLOCKED`           | `disable_read_only_mode`                     |

---

## Read-only (safe) mode

Because openLCA databases can hold valuable modeling work, agents should default
to read-only access and only enable writes deliberately.

```python
from openlca_ipc import OLCAClient
from openlca_ipc.agent import WriteBlocked

with OLCAClient(port=8080, read_only=True) as client:
    flows = client.search.find_flows(['steel'])     # OK
    result = client.calculate.simple_calculation(system, method)  # OK
    try:
        client.data.create_product_flow("Widget")   # raises
    except WriteBlocked as e:
        handle(e.to_dict())
```

In read-only mode every database mutation (`put`, `delete`,
`create_product_system`, ...) raises `WriteBlocked` before reaching the server.
Reads, searches, and calculations are unaffected.

---

## Reliability checks

`check_result_consistency` returns warning strings (it never raises), so you can
surface them in a `ResultSummary.warnings` list or assert on them in tests.

```python
from openlca_ipc import check_result_consistency

warnings = check_result_consistency(result)
summary = ResultSummary.from_impacts(impacts, warnings=warnings)
```

It currently verifies that per-process contributions sum to each category total
within tolerance — a mismatch usually signals broken provider linking or a
partially-computed result.

---

## Building an MCP server on top

A thin MCP layer can map tools directly onto these helpers:

| MCP tool                  | Backed by                                             |
| ------------------------- | ----------------------------------------------------- |
| `openlca_health`          | `health_check(client)`                                |
| `openlca_search`          | `client.search.*` → `EntitySummary`                   |
| `openlca_calculate`       | `client.calculate.simple_calculation` → `ResultSummary` |
| `openlca_contribution_tree` | `client.contributions.get_contribution_tree`        |
| `openlca_compare_scenarios` | `client.calculate.compare_systems`                  |
| `openlca_export_result`   | `client.export.*` + `CalculationContext`              |

Keep the MCP layer focused on tool schemas, permissions, and structured output;
keep openLCA-specific logic here in the package.
