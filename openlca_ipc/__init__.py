# ============================================================================
# OpenLCA Utils - Professional Python Library
# ============================================================================
# A comprehensive utility library for openLCA IPC operations
# Compatible with: olca-ipc 2.6+, olca-schema 2.6+, openLCA 2.x
# ============================================================================

"""
openlca_ipc: Professional utilities for openLCA IPC operations

This package provides high-level utilities for working with openLCA through
the IPC protocol, making LCA workflows easier and more maintainable.

Based on olca-ipc 2.6+ and olca-schema 2.6+, this library follows
ISO-14040/14044 standards for life cycle assessment (LCA) workflows.
"""

__version__ = "0.4.1"
__author__ = "Ernest Boakye Danquah"

from .client import OLCAClient
from .search import SearchUtils
from .data import DataBuilder
from .systems import SystemBuilder
from .calculations import CalculationManager
from .results import ResultsAnalyzer
from .contributions import ContributionAnalyzer, ContributionItem, TreeNode
from .uncertainty import UncertaintyAnalyzer
from .parameters import ParameterManager
from .export import ExportManager
from .diagnostics import check_result_consistency
from . import agent
from .agent import (
    EntitySummary,
    ResultSummary,
    CalculationContext,
    health_check,
    OLCAError,
)

__all__ = [
    'OLCAClient',
    'SearchUtils',
    'DataBuilder',
    'SystemBuilder',
    'CalculationManager',
    'ResultsAnalyzer',
    'ContributionAnalyzer',
    'ContributionItem',
    'TreeNode',
    'UncertaintyAnalyzer',
    'ParameterManager',
    'ExportManager',
    # Accuracy / reliability
    'check_result_consistency',
    # Agent layer
    'agent',
    'EntitySummary',
    'ResultSummary',
    'CalculationContext',
    'health_check',
    'OLCAError',
]
