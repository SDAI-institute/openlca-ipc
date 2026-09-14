# Tutorials

These tutorials build from a verified connection to reproducible analysis. Use a disposable or test database for exercises that create data.

## Learning path

1. **Connect and inspect** — start openLCA IPC, test the connection, search entities, and verify the active database.
2. **Build a foreground process** — create a product flow, exchanges, a process, and check its mass balance.
3. **Create a product system** — choose provider-linking behavior and inspect the generated network.
4. **Calculate impacts** — run one LCIA method, extract totals and inventory, then dispose the result.
5. **Interpret hotspots** — process/flow contributions, contribution trees, total requirements, and Sankey data.
6. **Compare scenarios** — explicit parameter redefinitions and system-to-system comparisons.
7. **Evaluate uncertainty** — Monte Carlo analysis with documented distributions and iteration settings.
8. **Automate safely** — read-only mode, structured agent responses, reproducibility context, and result consistency checks.

## Existing runnable material

The repository `examples/` directory contains runnable scripts and notebooks. The package test suite also includes synthetic and regression fixtures useful for understanding expected behavior.

For a short first workflow, start with [Quick Start](../quickstart.md). For exact methods, use the [API Reference](../api/README.md). For automation, use [Agent & MCP Usage](../agent-usage.md).

## Publication rule

Example output is not automatically a benchmark. When reporting results publicly, record the exact database/model, method, package/source revision, functional basis, parameters, and limitations.