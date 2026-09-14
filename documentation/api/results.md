# ResultsAnalyzer API

`ResultsAnalyzer` converts live openLCA result objects into smaller Python dictionaries for review, export, visualization, and downstream automation.

## `get_total_impacts(result)`

Returns impact-category totals with category reference, amount, and unit.

## `get_inventory(result, *, direction="both")`

Returns the total elementary-flow inventory. `direction` can be `input`, `output`, or `both`. Rows include flow reference, amount, direction, unit, and location where available.

## `get_normalized_impacts(result)`

Returns normalized impacts when the selected LCIA method supplies a normalization set. Returns an empty list when normalization is unavailable.

## `get_weighted_impacts(result)`

Returns weighted impacts when weighting is available for the method.

## `get_total_requirements(result)`

Returns the scaled technology requirements of the product system: provider/process, flow, and amount.

## `get_sankey(result, impact_category, *, max_nodes=50, min_share=0.0)`

Requests upstream Sankey graph data from openLCA and serializes it into plain node/edge data suitable for a visualization or structured client response.

## Example

```python
result = client.calculate.simple_calculation(system, method)
try:
    totals = client.results.get_total_impacts(result)
    inventory = client.results.get_inventory(result, direction="output")
    requirements = client.results.get_total_requirements(result)
finally:
    result.dispose()
```

## Review points

Empty normalized/weighted results can mean the method does not define those factors; they are not automatically calculation failures. Preserve the impact-category IDs and study context when exporting result tables.