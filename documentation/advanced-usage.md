# Advanced Usage

Advanced openLCA IPC work is less about calling more methods and more about controlling model identity, result lifecycle, scenarios, uncertainty, and provenance.

## Use read-only mode for inspection and agent workflows

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080, read_only=True) as client:
    flow = client.search.find_flow(["steel"])
```

Searches and calculations remain available; database writes are blocked at the Python layer.

## Capture calculation provenance

Use `CalculationContext.capture(...)` from the agent layer to retain package versions, database identity, product-system/method references, functional unit, settings, timestamp, and result identifier.

## Check result consistency

`check_result_consistency(result)` verifies that process contributions sum to reported category totals within tolerance. Treat warnings as a review trigger, not as a substitute for broader model validation.

## Compare systems under one controlled basis

`client.calculate.compare_systems(...)` calculates two systems on the same method/reference amount and disposes intermediate results automatically. Confirm that functional units and boundaries are truly comparable before interpreting percentage differences.

## Run parameter scenarios safely

`client.parameters.run_scenario_analysis(...)` validates that a global parameter exists before varying it. For local parameters, supply the owning process/method context explicitly.

## Monte Carlo uncertainty

Use `client.uncertainty.run_monte_carlo(...)` after distributions are reviewed. Record iteration count and uncertainty assumptions; numerical sampling does not create uncertainty information that the model does not contain.

## Inspect upstream structure

Contribution trees and Sankey data expose modeled upstream drivers. Use depth/share limits to keep analysis bounded, and inspect unexpected hotspots against provider linking, database geography, allocation, and units.

## Reproducible automation pattern

1. Record environment and active database.
2. Resolve model entities by ID/name and verify them.
3. Freeze functional basis, method, parameters, and allocation.
4. Calculate once.
5. Run consistency checks and interpretation calls on that result.
6. Export results with context.
7. Dispose the live result.
8. Archive the evidence package and limitations.

See [Agent & MCP usage](agent-usage.md) for structured automation responses.