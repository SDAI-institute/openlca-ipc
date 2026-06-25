# ============================================================================
# OpenLCA Utils - Professional Python Library
# ============================================================================
# A comprehensive utility library for openLCA IPC operations
# Compatible with: olca-ipc 2.4.0, olca-schema 2.4.0, openLCA 2.x
# ============================================================================

"""
openlca_ipc: Professional utilities for openLCA IPC operations

This package provides high-level utilities for working with openLCA through
the IPC protocol, making LCA workflows easier and more maintainable.

Based on olca-ipc 2.4.0 and olca-schema 2.4.0, this library follows
ISO-14040/14044 standards for life cycle assessment (LCA) workflows.
"""

__version__ = "0.2.0"
__author__ = "Ernest Boakye Danquah"

# Import core functionality
try:
    from .client import OLCAClient
    from .search import SearchUtils
    from .data import DataBuilder
    from .systems import SystemBuilder
    from .calculations import CalculationManager
    from .results import ResultsAnalyzer
    from .contributions import ContributionAnalyzer
    from .uncertainty import UncertaintyAnalyzer
    from .parameters import ParameterManager
    from .export import ExportManager

    __all__ = [
        'OLCAClient',
        'SearchUtils',
        'DataBuilder',
        'SystemBuilder',
        'CalculationManager',
        'ResultsAnalyzer',
        'ContributionAnalyzer',
        'UncertaintyAnalyzer',
        'ParameterManager',
        'ExportManager'
    ]
except ImportError as e:
    print(f"Warning: Could not import OLCAClient or utility classes: {e}")
    OLCAClient = None
    __all__ = []
