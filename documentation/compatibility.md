# Compatibility and Verified Environment

This page separates the package's declared requirements from the specific environment SDAI has recorded during integration work.

## Package requirements

For `openlca-ipc` 0.4.1:

| Component | Declared requirement |
|---|---|
| Python | 3.11 or newer |
| `olca-ipc` | 2.6.0 or newer |
| `olca-schema` | 2.6.0 or newer |
| NumPy | 1.24 or newer |
| openLCA Desktop | 2.x with IPC Server enabled |

Optional analysis/export dependencies are installed through the package extras described in `pyproject.toml`.

## SDAI verified integration snapshot

The SDAI research MCP stack documented on 2026-09-13 used openLCA Desktop **2.5.0** with the desktop IPC server on port 8080. The saved functional-smoke record confirmed a live database connection and successful entity-count queries through the MCP/library path.

This validates that specific integration snapshot. It does not imply that every openLCA 2.x point release, database, or plugin combination has been tested.

## Source basis

The reviewed library source basis is:

```text
package: openlca-ipc 0.4.1
branch: main
reviewed revision: a6410ba10cb186f9c01275584594ebe25418ddc0
review date: 2026-09-13
```

Public documentation should identify both the package version and the source revision when behavior beyond the released API surface is discussed.

## Database and method compatibility

`openlca-ipc` communicates with whichever database is active in openLCA Desktop. Compatibility with the IPC protocol does not validate:

- the database's licensing or redistribution rights;
- the completeness of a foreground system;
- provider links;
- flow properties or unit choices;
- allocation/cutoff decisions;
- LCIA method suitability;
- normalization or weighting availability.

Record database name/version and LCIA method identity with every decision-relevant result.

## Upgrade checklist

When changing openLCA Desktop, `olca-ipc`, `olca-schema`, or this package:

1. create or select a controlled test database;
2. run connection/search smoke checks;
3. rerun the synthetic golden/reference calculation where available;
4. check non-mass exchange unit handling;
5. verify contribution/result consistency;
6. run scenario and uncertainty smoke tests used by your workflow;
7. record the new versions and source revision;
8. update this matrix only after the checks pass.

## Status vocabulary

Use **declared requirement** for metadata constraints, **verified snapshot** for an environment that was actually exercised, and **supported/validated** only within the explicitly tested scope.