# CalculationManager API

`CalculationManager` builds calculation setups, executes openLCA calculations, and provides deterministic system-to-system comparison helpers.

## `simple_calculation(system, impact_method=None, amount=1.0, *, allocation=None)`

Runs a calculation for a product system and waits for the openLCA result to become ready.

- `system` — product-system `Ref`.
- `impact_method` — optional `ImpactMethod` or compatible reference.
- `amount` — reference amount for the calculation.
- `allocation` — optional openLCA allocation type for multi-output processes.

The returned live result must be disposed when analysis is complete.

```python
result = client.calculate.simple_calculation(system, method, amount=1.0)
try:
    impacts = client.results.get_total_impacts(result)
finally:
    result.dispose()
```

## `contribution_analysis(system, impact_method, amount=1.0)`

Runs an impact calculation suitable for subsequent process, flow, or upstream contribution analysis. The returned result has the same lifecycle requirement: dispose it when finished.

## `compare_systems(system1, system2, impact_method, amount=1.0)`

Calculates both systems on the same impact method, aligns total impacts by category name, and returns:

```text
category -> system1, system2, difference, percent_diff
```

Both intermediate results are disposed internally.

## Reproducibility guidance

Record the active database, product-system IDs, impact-method ID, reference amount, allocation choice, package/openLCA versions, and relevant parameters alongside reported results. Re-running a calculation against a changed database or model is not the same experiment.