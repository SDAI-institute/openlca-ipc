# SystemBuilder API

`SystemBuilder` creates calculation-ready product systems from a root process and an explicit linking configuration.

## `create_product_system(process, name=None, default_providers="prefer", preferred_type="LCI_RESULT", cutoff=None)`

Creates and auto-links a product system from a process or process reference.

### Parameters

- `process` — root `Process` or `Ref`.
- `name` — optional post-creation name.
- `default_providers` — `prefer`, `only`, or `ignore`.
- `preferred_type` — `LCI_RESULT` or `UNIT_PROCESS`.
- `cutoff` — optional linking cutoff in the interval `[0, 1)`.

### Provider-linking behavior

`prefer` uses configured default providers where present and links freely otherwise. `only` uses only default providers. `ignore` ignores default-provider assignments during linking.

### Example

```python
process = client.search.find_processes(["Widget production"])[0]
system = client.systems.create_product_system(
    process,
    default_providers="prefer",
    preferred_type="UNIT_PROCESS",
    cutoff=0.01,
)
```

## Review points

- Product-system creation writes to the active database.
- A successful linking operation does not prove that the selected providers are methodologically appropriate.
- Record the root process, linking policy, cutoff, active database, and resulting system ID in reproducible studies.
- Inspect unlinked exchanges before trusting a calculation.