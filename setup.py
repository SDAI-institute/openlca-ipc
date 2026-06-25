# All package metadata now lives in pyproject.toml (the single source of truth).
# This shim remains only for tooling that still invokes setup.py directly.
from setuptools import setup

setup()