# UncertaintyAnalyzer API

`UncertaintyAnalyzer` runs Monte Carlo simulations through openLCA and summarizes the resulting impact distributions.

## `run_monte_carlo(system, impact_method, iterations=1000, amount=1.0, progress_callback=None)`

Runs an openLCA simulation result repeatedly and returns one `UncertaintyResult` per impact category.

Each result contains the sampled values, mean, standard deviation, median, 5th percentile, 95th percentile, and coefficient of variation. The underlying simulation result is disposed in a `finally` block.

```python
results = client.uncertainty.run_monte_carlo(
    system,
    method,
    iterations=1000,
)

for name, stats in results.items():
    print(name, stats.mean, stats.percentile_5, stats.percentile_95)
```

## `compare_with_uncertainty(system1, system2, impact_method, iterations=1000)`

Runs Monte Carlo simulations for two systems and reports per-category summary statistics plus an independent-samples t-test.

## Interpretation guidance

Monte Carlo output is only as meaningful as the uncertainty distributions encoded in the underlying model. A narrow numerical interval does not establish complete data quality, and a p-value is not a substitute for practical or methodological interpretation.

Record the number of iterations, software/database versions, model parameterization, random/simulation settings when available, and whether the comparison assumptions are truly comparable.