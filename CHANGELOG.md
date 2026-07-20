# Changelog

All notable changes to **openlca-ipc** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-07-01

### Fixed (correctness — surfaced by reproducing the openLCA PET-vs-PC tutorial)

- **`DataBuilder.create_exchange` no longer hardcodes Mass/kg.** It now derives
  the exchange's flow property and unit from the flow's **reference flow
  property**, so non-mass flows (e.g. transport in `t*km`, energy in `MJ`) are
  measured correctly. Previously every exchange was forced to Mass/kg; openLCA
  silently dropped the invalid unit on a `t*km` transport flow and fell back to
  its reference unit, inflating a `0.065*500 kg*km` (=0.0325 t*km) transport
  input to **32.5 t*km — a ~1000× error** that dominated results. New optional
  keyword args: `unit`, `flow_property` (overrides) and `formula` (stores an
  openLCA amount formula such as `"0.065*500"`). Mass-flow behaviour unchanged.
- **`ExportManager.export_impacts_to_csv` no longer crashes** with
  `dict contains fields not in fieldnames: 'category'`. Header is now built from
  the keys actually present, nested objects are flattened, and
  `extrasaction='ignore'` guards unexpected keys.
- **`SearchUtils.find_impact_method` is version-noise tolerant.** `['EF v3.1']`
  now resolves to `"EF 3.1 Method (adapted)"` (previously returned `None`). Added
  `find_impact_methods(keywords, max_results=10)` returning ranked candidates.
- **`ParameterManager.run_scenario_analysis` fails loudly on unknown
  parameters** instead of silently returning the baseline for every value.
  Added `find_global_parameter(name)`.

### Added

- **`SystemBuilder.create_product_system(..., cutoff=<float>)`** exposes the
  linking cut-off (openLCA tutorial ch. 6.3 uses `0.05` for a 5% cut-off).
- **`DataBuilder.check_mass_balance(process, *, rel_tol=1e-3)`** — flags
  processes whose Mass-property inputs and outputs don't balance (the
  tutorial explicitly warns openLCA does not check this automatically).

### Testing (bug-class prevention + regression guards)

- **Unit-fuzzing** (`tests/test_data.py`, `tests/test_unit_fuzzing_live.py`):
  parametrized mocked + live tests across Mass, Energy, Volume, Land use,
  Goods transport, and Number-of-items flow properties, plus a regression
  guard that the reference unit is chosen via `is_ref_unit`, not list order or
  a `conversion_factor == 1.0` coincidence — this exact ambiguity was a latent
  bug in the initial `create_exchange` fix, caught by writing this test suite.
- **Provider-location invariants** (`tests/test_search_live.py`): every
  `find_providers` result carries a `location`, and same-named providers are
  always distinguished by it — the condition whose absence caused the
  original F3 defect.
- **Synthetic golden system** (`tests/fixtures/golden_system.py`,
  `tests/test_golden_live.py`): a fully synthetic, license-free system (custom
  elementary flow + impact method/category + 2-level process chain) with a
  hand-derived expected answer (6.5 kg CO2e) — an independent cross-check that
  needs no external database, plus a determinism regression (5 repeated
  calculations must be identical).
- **PET/PC regression baseline** (`tests/fixtures/pet_system.py` — shared with
  `case1_repeatability.ipynb` — `tests/fixtures/pet_golden.json`,
  `tests/test_golden_pet_live.py`): locks in our own verified post-fix PET/PC
  results as a regression guard, independent of the tutorial PDF's published
  numbers (which differ by a known, root-caused ~0.78x background-dataset
  factor — see `openlca-ipc case studies/case1-findings.md`).

## [0.4.0] - 2026-06-25

### Added

**New result methods (all additive — no breaking changes to v0.3 surface):**
- `ContributionAnalyzer.get_contribution_tree(result, impact_category, *, max_depth=3, min_share=0.01)` — recursively expands upstream process contributions into a nested `TreeNode` dataclass tree, pruned by depth and minimum share threshold.
- `ResultsAnalyzer.get_inventory(result, *, direction='both')` — full elementary-flow inventory from `result.get_total_flows()`; filterable by `'input'`/`'output'`/`'both'`.
- `ResultsAnalyzer.get_normalized_impacts(result)` — normalized impact results as consistent `{name, category, amount, unit}` dicts.
- `ResultsAnalyzer.get_weighted_impacts(result)` — weighted impact results in the same shape.
- `ResultsAnalyzer.get_total_requirements(result)` — technology-matrix scaling vector: `[{process, provider, flow, amount}]`.
- `ResultsAnalyzer.get_sankey(result, impact_category, *, max_nodes=50, min_share=0.0)` — builds `SankeyRequest`, calls `result.get_sankey_graph()`, returns nodes/edges as plain dicts ready for visualization or MCP tools.
- `CalculationManager.compare_systems(system1, system2, impact_method, amount=1.0)` — runs both systems and returns per-category `{system1, system2, difference, percent_diff}`.
- `SearchUtils.get_by_name(model_type, name)` — exact entity lookup via `client.find(type, name)`.

**Agent layer (`openlca_ipc.agent` subpackage — new):**
- `ResultSummary` / `EntitySummary` — compact JSON-ready summaries with `.to_dict()` / `.to_json()` matching the about-doc payload shape; includes `top_impacts`, `next_actions`, and `warnings`.
- `CalculationContext.capture(...)` — captures database identity, library versions, product system, functional unit, impact method, settings, ISO-8601 timestamp, and a generated `result_id` for reproducible artifacts.
- `OLCAError` base class and subclasses (`ConnectionFailed`, `ImpactMethodNotFound`, `SystemNotFound`, `EntityNotFound`, `CalculationFailed`, `WriteBlocked`) — structured recoverable error envelopes with `error_code`, `recoverable`, and `suggested_next_actions`.
- `health_check(client, *, count_entities=True)` — connection probe returning entity counts; backs an `openlca_health` MCP tool.
- `OLCAClient(read_only=True)` — `_ReadOnlyGuard` proxy blocks all write methods (`put`, `delete`, `create_product_system`, …) with `WriteBlocked` before reaching the server; reads and calculations unaffected.

**Diagnostics:**
- `openlca_ipc.diagnostics.check_result_consistency(result, *, rel_tol=1e-3, abs_tol=1e-12) -> list[str]` — returns warning strings when per-process contributions don't sum to the category total; empty list = all checks passed.

**Tests:**
- `tests/test_new_functions.py` — contribution tree (nested, depth pruning, min-share pruning, error); inventory (direction filter, sort); normalized/weighted/requirements/sankey; `compare_systems`; `get_by_name`.
- `tests/test_agent.py` — `ResultSummary` shape, `CalculationContext` auto-fill, error envelopes, `health_check`, `_ReadOnlyGuard` write blocking, `OLCAClient(read_only=True)`.
- `tests/test_diagnostics.py` — warnings fire on inconsistent mocked results, silent on consistent.
- `tests/test_validation.py` (`@pytest.mark.live`) — 5 live accuracy tests: wrapper totals match raw openLCA within tolerance; contributions sum to total; tree root matches total; inventory non-empty; consistency check passes.
- Mocked suite: 118 tests, 95% coverage. Live suite: 18 tests pass on port 8080.

**Documentation:**
- `documentation/quickstart.md` updated with v0.4 patterns: contribution tree, inventory, normalization, `ResultSummary.to_json()`, read-only mode.
- New `documentation/agent-usage.md` — MCP builder guide: health check, summaries, reproducibility, error hierarchy, read-only mode, building an MCP layer.
- New `documentation/api/agent.md` — agent subpackage API reference.
- `documentation/api/README.md` updated with v0.4 methods and agent/ link.

### Changed
- `OLCAClient.__init__` gains `read_only: bool = False` (backwards-compatible; default `False` preserves v0.3.0 behaviour).
- `__init__.py` exports: `TreeNode`, `check_result_consistency`, `agent` subpackage, `EntitySummary`, `ResultSummary`, `CalculationContext`, `health_check`, `OLCAError`.

---

## [0.3.0] - 2026-06-25

### Fixed
- **Context-manager exit no longer crashes** — `OLCAClient.__exit__` previously called
  `self.client.close()`, which does not exist on `olca_ipc.Client 2.6+`. The method now
  guards with `getattr(..., 'close', None)` so `with OLCAClient() as c:` is safe.
- **`ContributionAnalyzer` completely rewritten** — old code called
  `client.lcia_process_contributions()` / `client.lcia_flow_contributions()`, neither of
  which exists in olca_ipc 2.x. Contributions are now read from the `Result` object
  (`result.get_impact_contributions_of()` / `result.get_flow_impacts_of()`) in line with
  the actual 2.6 API. Every contribution call previously silently returned `[]`.
- **`UncertaintyAnalyzer` Monte Carlo rewritten** — replaced the nonexistent
  `client.simulator()` / `next_simulation()` / `client.dispose()` calls with the correct
  `client.simulate()` → `result.simulate_next()` → `result.dispose()` pattern.
- **`SystemBuilder.create_product_system`** now wires `default_providers` and
  `preferred_type` into an `o.LinkingConfig` that is passed to the client (params were
  silently ignored before). Uses `client.put()` (not the nonexistent `client.update()`).
- **`ExportManager.export_to_excel`** rewritten to use `openpyxl` directly
  (old code called nonexistent `client.excel_export()`).
- **`SearchUtils.find_impact_method`** now uses `all(keywords)` for multi-keyword
  matching, consistent with `find_flows`/`find_processes`. Removed dead `get_providers_of`
  branch.
- **`CalculationManager`** accepts either `o.ImpactMethod` or `o.Ref` for `impact_method`;
  normalises via `to_ref()` guard.
- **`ResultsAnalyzer`** narrows bare `except` to `except Exception as e` and guards
  `None` amounts.

### Changed
- **Mock suite upgraded to `spec`-constrained mocks** — all tests now use
  `MagicMock(spec=ipc.Client)` and `MagicMock(spec=ipc.Result)` so calls to nonexistent
  methods raise `AttributeError` immediately. Coverage: 95% (up from 31%).
- **`simple_client.py` removed** — duplicate `OLCAClient` with all utility attrs `None`
  and 0% coverage. Not exported; pure confusion.
- **`__init__.py` no longer swallows `ImportError`** — import failures are now loud.
- Compatibility note updated to `olca-ipc 2.6+ / olca-schema 2.6+`.
- `openpyxl>=3.1.0` added to `[full]` and `[dev]` extras; `scipy>=1.10.0` added to `[dev]`.

### Added
- `tests/test_contributions.py` — 15 tests covering process/flow contributions, share
  calculation, min-share filtering, sorting, and error paths.
- `tests/test_results.py` — 5 tests including None-amount guard and error path.
- `tests/test_systems.py` — 6 tests verifying `LinkingConfig` passthrough.
- `tests/test_parameters.py` — 7 tests covering scenario analysis and Ref passthrough.
- `tests/test_export.py` — 10 tests for Excel, CSV, and comparison exports.
- `tests/test_uncertainty.py` — 7 tests verifying Monte Carlo iteration count, `dispose()`
  in `finally`, stat computation, and progress callbacks.
- `tests/test_live_integration.py` — 13 live integration tests (`@pytest.mark.live`),
  excluded from CI; cover a full connect→search→build→calculate→contributions round trip.
- `.github/workflows/ci.yml` — Python 3.11/3.12/3.13 matrix; mocked tests + flake8/black.

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

[0.3.0]: https://github.com/dernestbank/openlca-ipc/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dernestbank/openlca-ipc/releases/tag/v0.2.0
[0.1.1]: https://github.com/dernestbank/openlca-ipc/releases/tag/v0.1.1
[0.1.0]: https://github.com/dernestbank/openlca-ipc/releases/tag/v0.1.0
