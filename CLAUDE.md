# CLAUDE.md — `openlca-ipc`

Project guidance for Claude Code working in this repository.

## What this is

`openlca-ipc` is a published PyPI wrapper around GreenDelta's `olca_ipc` / `olca_schema` that exposes a
facade `OLCAClient` plus utility managers for LCA workflows. It is the reusable Python foundation under a
future **OpenLCA-MCP**. Design intent and the agent-oriented roadmap live in
`../dev-actions/about_openlca-ipc.md`; the active implementation checklist is
`../dev-actions/openlca-ipc_test-paln1.2.md`.

- Repo remote: `https://github.com/SDAI-institute/openlca-ipc.git`
- PyPI: https://pypi.org/project/openlca-ipc/
- Public surface is **stable** — prefer additive changes; don't break existing manager signatures.

## Environment

- Python venv (uv-managed, **no `pip`**): `../AI Agents for ESG/.venv`
  - Interpreter: `D:/01code/Projects/SDAI- Ecosystem/AI Agents for ESG/.venv/Scripts/python.exe`
- Install / add deps with **uv**, never pip:
  ```bash
  uv pip install --python "D:/01code/Projects/SDAI- Ecosystem/AI Agents for ESG/.venv/Scripts/python.exe" -e ".[dev]"
  ```
- Installed: `olca-ipc==2.6.3`, `olca-schema==2.6.2`. openLCA desktop IPC server runs on **port 8080**
  (disposable/scratch DB — live tests may create/calculate against it).

## Testing

```bash
PY="D:/01code/Projects/SDAI- Ecosystem/AI Agents for ESG/.venv/Scripts/python.exe"
"$PY" -m pytest            # mocked suite (live tests deselected by default)
"$PY" -m pytest -m live    # live integration tests (needs IPC server on 8080)
```

- Mocks use `MagicMock(spec=ipc.Client)` / `spec=ipc.Result` so calls to nonexistent olca_ipc methods fail
  loudly — keep that discipline; it has caught real bugs.

## Release / publish runbook

Version is declared in **two** places that must stay in sync: `openlca_ipc/__init__.py` (`__version__`) and
`pyproject.toml` (`version`). Also add a `CHANGELOG.md` entry.

```bash
PY="D:/01code/Projects/SDAI- Ecosystem/AI Agents for ESG/.venv/Scripts/python.exe"
"$PY" -m build                       # builds sdist + wheel into dist/
"$PY" -m twine check dist/*          # validate metadata
"$PY" -m twine upload dist/<name>-<version>*   # publish (IRREVERSIBLE — confirm with user first)
```

### PyPI credentials

The PyPI API token is stored in the **gitignored** `.pypirc` in this directory (section `[pypi]`,
`username = __token__`). `twine upload` reads it automatically — no need to pass credentials on the command
line. **Never** copy the token value into any tracked file (including this one), into commit messages, or into
chat output. `.pypirc` and `.secrets/` are gitignored; keep it that way. TestPyPI creds are under `[testpypi]`.

If a token must be supplied explicitly, read it at upload time only, e.g.
`TWINE_PASSWORD=$(grep -A2 '\[pypi\]' .pypirc | grep password | cut -d= -f2 | xargs)` — do not echo it.

## Conventions

- Git commit message trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Commit/push only when asked. Branch before committing if on the default branch.
- `pyproject.toml` `[project.urls]` still points at `github.com/dernestbank/...` while the real remote is
  `github.com/SDAI-institute/...` — reconcile these when next editing packaging metadata.
