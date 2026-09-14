# openLCA IPC Documentation Map

This map points to the current documentation set for `openlca-ipc` 0.4.1. The package source and `pyproject.toml` remain authoritative for implementation behavior and declared dependencies.

## Start here

1. [Installation](installation.md) — Python/openLCA prerequisites and package setup.
2. [Quick start](quickstart.md) — first controlled openLCA workflow.
3. [User guide](user-guide.md) — how the modules fit into a complete study workflow.
4. [Compatibility](compatibility.md) — declared requirements versus the verified SDAI environment.

## Core API reference

- [API overview](api/README.md)
- [OLCAClient](api/client.md)
- [Search utilities](api/search.md)
- [DataBuilder](api/data.md)
- [SystemBuilder](api/systems.md)
- [CalculationManager](api/calculations.md)
- [ResultsAnalyzer](api/results.md)
- [ContributionAnalyzer](api/contributions.md)
- [UncertaintyAnalyzer](api/uncertainty.md)
- [ParameterManager](api/parameters.md)
- [ExportManager](api/export.md)

## Applied use

- [Tutorial path](tutorials/README.md)
- [Advanced usage](advanced-usage.md)
- [Agent and MCP automation](agent-usage.md)
- [Best practices](best-practices.md)
- [Examples](../examples/README.md)

## Reference and troubleshooting

- [Compatibility and verified environment](compatibility.md)
- [Troubleshooting](troubleshooting.md)
- [FAQ](faq.md)
- [Migration guide](migration.md)

## Development and validation

- [Development setup](development.md)
- [Testing guide](testing.md)
- [Changelog](../CHANGELOG.md)
- [Source repository](https://github.com/SDAI-institute/openlca-ipc)

## Recommended paths by role

### LCA practitioner

Installation → Quick start → User guide → Results → Contributions → Parameters/Uncertainty → Best practices.

### Developer

Installation → API overview → individual module references → Development → Testing → Changelog.

### Automation / MCP developer

Quick start → Agent and MCP automation → Compatibility → Calculations → Results → Contributions → Parameters → Testing.

### Reviewer / researcher

Compatibility → User guide → Best practices → Testing → the exact module references used by the study. Review the evidence package separately from the API documentation.

## Documentation source rules

- Correct technical behavior in the owning source first.
- Keep version and compatibility claims tied to a package/source revision.
- Do not describe an untested environment as validated.
- Distinguish calculation reproducibility from methodological validity.
- Preserve result disposal and study-provenance requirements in examples.

## Current source basis

```text
package: openlca-ipc 0.4.1
reviewed source: main @ a6410ba10cb186f9c01275584594ebe25418ddc0
reviewed: 2026-09-13
```

Local documentation improvements made after that reviewed code revision must be committed and re-pinned before a public release claims the documentation itself is represented by that git SHA.
