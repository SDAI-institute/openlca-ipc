# ExportManager API

`ExportManager` writes reviewed calculation outputs to portable files. Export does not freeze the underlying model by itself; preserve the study context and source identifiers alongside each file.

## `export_to_excel(result, filepath)`

Writes total impact results to an Excel workbook using `openpyxl`. Install the export extra when needed:

```bash
pip install "openlca-ipc[export]"
```

## `export_impacts_to_csv(impacts, filepath)`

Writes a list of impact dictionaries to CSV. v0.4.1 builds the header from the keys actually present and flattens nested objects such as category references into readable scalar values.

```python
impacts = client.results.get_total_impacts(result)
client.export.export_impacts_to_csv(impacts, "impacts.csv")
```

## `export_comparison_to_csv(comparison_data, filepath)`

Writes the output of `CalculationManager.compare_systems()` with system 1, system 2, absolute difference, and percentage difference for each impact category.

## Recommended artifact metadata

For decision-relevant exports, save or accompany the file with:

- package version and source revision;
- openLCA version and active database/version;
- product-system ID and reference amount;
- impact-method ID/version;
- scenario/parameter state;
- timestamp;
- calculation/review notes.

The `openlca_ipc.agent.CalculationContext` helper can provide much of this context for machine-readable artifacts.