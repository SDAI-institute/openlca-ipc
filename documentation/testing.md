# Testing Guide

The project separates mocked/unit coverage from tests that require a real openLCA instance.

## Default test suite

```bash
pytest
```

`pyproject.toml` excludes the `live` marker by default and measures coverage for `openlca_ipc`.

## Live tests

Start openLCA Desktop, load the intended database, and start the IPC server. Then run:

```bash
pytest -m live
```

Set `OLCA_IPC_PORT` when the server is not on 8080.

## Validation tiers

- Basic live integration: connection, search, create, calculate, and contributions.
- Synthetic golden system: license-free system with a hand-derived expected answer and repeatability check.
- Unit/provider invariant tests: non-mass unit derivation and provider geography behavior.
- PET/PC regression: database-specific regression fixture for the verified tutorial reproduction.

## Test hygiene

Live tests that create entities use distinctive names and teardown logic. Use a test/scratch database when possible. If a run is interrupted, inspect the openLCA Navigator for leftover test-prefixed entities before continuing.

## What passing tests mean

A passing software test validates the tested behavior in the specified environment. It does not certify a database, foreground model, LCIA method, or study conclusion.