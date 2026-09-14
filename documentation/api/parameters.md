# ParameterManager API

`ParameterManager` creates openLCA parameter redefinitions and runs explicit one-parameter scenario sweeps.

## `create_parameter_redef(name, value, context=None)`

Builds an `olca_schema.ParameterRedef`. `context=None` represents a global parameter; a process or method reference can be supplied for a contextual parameter.

## `find_global_parameter(name)`

Performs an exact, case-insensitive lookup over global parameter descriptors and returns the matching reference or `None`.

## `run_scenario_analysis(system, impact_method, parameter_name, values, context=None)`

Runs one calculation per supplied parameter value and returns a mapping from value to impact-result rows.

The implementation deliberately fails when a named global parameter cannot be found. openLCA can otherwise ignore an invalid parameter redefinition, creating a dangerous false scenario in which every run silently reproduces the baseline.

```python
scenarios = client.parameters.run_scenario_analysis(
    system=system,
    impact_method=method,
    parameter_name="transport_distance",
    values=[100, 500, 1000],
)
```

## Reproducibility guidance

Record the parameter name, scope/context, units, baseline value, scenario values, product system, method, and reference amount. Verify that the parameter actually affects the intended exchanges or formulas before interpreting a sensitivity trend.