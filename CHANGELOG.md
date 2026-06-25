# Changelog

All notable changes to **openlca-ipc** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-25

### Fixed
- Repaired the entire test suite, which had drifted out of sync with the code.
  Tests now exercise the real public signatures (`create_product_flow(name, description)`,
  `create_exchange(..., is_quantitative_reference=...)`, `simple_calculation(system=...)`,
  etc.) and the suite passes against `olca-ipc` 2.4.0 (32 tests).
- Corrected the mock patch target in the client tests
  (`openlca_ipc.client.ipc.Client` instead of the non-existent
  `openlca_ipc.client.olca.Client`).
- Resolved a packaging conflict: the project declared `requires-python = ">=3.10"`
  while depending on `olca-ipc>=2.4.0`, which requires Python **≥3.11**. A 3.10
  user could not actually install the library.
- Synced the version number across `pyproject.toml` and
  `openlca_ipc.__init__.__version__` (previously `0.1.1` vs `0.1.0`).
- Aligned `requirements.txt` (`olca-ipc>=2.4.0`, `olca-schema>=2.4.0`) with the
  ranges declared in `pyproject.toml` (was hard-pinned to `==2.4.0`).

### Changed
- **Minimum Python is now 3.11** (dropped 3.10). Updated classifiers, the Black
  `target-version`, and the mypy `python_version` accordingly.
- `pyproject.toml` is now the single source of truth for packaging metadata.
  `setup.py` is reduced to a thin `setup()` shim, removing the duplicated
  version/metadata that previously had to be kept in sync by hand.
- Added explicit package discovery (`[tool.setuptools.packages.find]` →
  `openlca_ipc*`) so tests, examples, and docs are excluded from the wheel.

## [0.1.1] - 2025-11

### Added
- Custom PyPI README and banner image.

## [0.1.0] - 2025-10

### Added
- Initial public release: `OLCAClient` plus `SearchUtils`, `DataBuilder`,
  `SystemBuilder`, `CalculationManager`, `ResultsAnalyzer`,
  `ContributionAnalyzer`, `UncertaintyAnalyzer`, `ParameterManager`, and
  `ExportManager`.

[0.2.0]: https://github.com/dernestbank/openlca-ipc/releases/tag/v0.2.0
[0.1.1]: https://github.com/dernestbank/openlca-ipc/releases/tag/v0.1.1
[0.1.0]: https://github.com/dernestbank/openlca-ipc/releases/tag/v0.1.0
