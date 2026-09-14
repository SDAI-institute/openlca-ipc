# User Guide

This guide connects the openLCA IPC package modules into a complete working pattern. For exact signatures, use the [API reference](api/README.md).

## 1. Connect to the intended database

Open openLCA Desktop, load the database you intend to use, and start **Tools → Developer Tools → IPC Server**. The default port is 8080.

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    assert client.test_connection()
```

Use `read_only=True` when a workflow should not modify the database.

## 2. Discover entities before creating or calculating

Use `client.search` to find flows, processes, providers, product systems, and LCIA methods. Preserve IDs and names in the study record; do not rely on the first fuzzy search match without review.

## 3. Build foreground data deliberately

`client.data` can create product flows, exchanges, and processes. v0.4.1 derives an exchange's default unit and property from the flow's reference flow property, including non-mass flows such as transport and energy.

Use `check_mass_balance()` for Mass-property exchanges and inspect provider links before creating a product system.

## 4. Build a product system

`client.systems.create_product_system()` exposes default-provider behavior, preferred process type, and optional linking cutoff. Record those choices; they materially affect the linked system.

## 5. Calculate and dispose

```python
result = client.calculate.simple_calculation(system, method, amount=1.0)
try:
    impacts = client.results.get_total_impacts(result)
finally:
    result.dispose()
```

Live results consume openLCA resources. Always dispose them when analysis is complete.

## 6. Interpret rather than only report totals

Use process/flow contributions, contribution trees, inventory results, total requirements, Sankey data, normalization/weighting, parameter scenarios, and Monte Carlo analysis where appropriate.

A calculation can be reproducible and still be methodologically wrong. Review functional unit, boundary, allocation, data quality, database geography/version, and LCIA method before making a decision claim.

## 7. Preserve reproducibility context

For important artifacts, record package/openLCA/database versions, product-system and method IDs, functional basis, parameters, allocation, source revision, timestamp, and limitations. `CalculationContext` in the agent layer can help produce a machine-readable record.

## Next

- [Quick start](quickstart.md)
- [API reference](api/README.md)
- [Agent & MCP usage](agent-usage.md)
- [Best practices](best-practices.md)
- [Troubleshooting](troubleshooting.md)
