# Development Setup

The package targets Python 3.11+.

```bash
git clone https://github.com/SDAI-institute/openlca-ipc.git
cd openlca-ipc
python -m venv .venv
# activate the environment for your platform
pip install -e ".[full]"
pip install -r requirements-dev.txt
```

## Source layout

- `openlca_ipc/client.py` — client composition and read-only guard.
- `search.py`, `data.py`, `systems.py` — model discovery and construction.
- `calculations.py`, `results.py`, `contributions.py` — execution and interpretation.
- `uncertainty.py`, `parameters.py`, `export.py` — advanced analysis and artifacts.
- `agent/` — structured summaries, provenance, errors, and health checks.
- `diagnostics.py` — result consistency checks.

## Quality checks

Use the repository configuration in `pyproject.toml` as the packaging source of truth.

```bash
pytest
black --check openlca_ipc tests
flake8 openlca_ipc tests
mypy openlca_ipc
```

The default pytest configuration excludes tests marked `live`. See [Testing](testing.md) for real-openLCA validation.