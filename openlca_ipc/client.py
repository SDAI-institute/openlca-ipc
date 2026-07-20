
# ============================================================================
# FILE: olca_utils/client.py
# ============================================================================

"""
Client management and connection utilities.
"""

import logging
from typing import Optional
import olca_schema as o
import olca_ipc as ipc

from .search import SearchUtils
from .data import DataBuilder
from .systems import SystemBuilder
from .calculations import CalculationManager
from .results import ResultsAnalyzer
from .contributions import ContributionAnalyzer
from .uncertainty import UncertaintyAnalyzer
from .parameters import ParameterManager
from .export import ExportManager
from .agent.errors import WriteBlocked

logger = logging.getLogger(__name__)

#: Underlying ipc.Client methods that mutate the database.
_WRITE_METHODS = frozenset({
    'put', 'put_all', 'delete', 'delete_all',
    'put_source_file', 'create_product_system',
})


class _ReadOnlyGuard:
    """
    Proxy around ``ipc.Client`` that blocks mutating calls.

    Read methods delegate to the wrapped client; any method in
    :data:`_WRITE_METHODS` raises :class:`~openlca_ipc.agent.errors.WriteBlocked`.
    Used when ``OLCAClient(read_only=True)`` so every manager that shares the
    client is prevented from mutating the database.
    """

    def __init__(self, client):
        object.__setattr__(self, '_client', client)

    def __getattr__(self, name):
        if name in _WRITE_METHODS:
            def _blocked(*args, **kwargs):
                raise WriteBlocked(operation=name)
            return _blocked
        return getattr(object.__getattribute__(self, '_client'), name)


class OLCAClient:
    """
    Main client wrapper for openLCA IPC operations.
    
    Provides organized access to all utility modules through a single interface.
    
    Attributes:
        client (ipc.Client): Underlying IPC client
        search (SearchUtils): Search utilities
        data (DataBuilder): Data creation utilities
        systems (SystemBuilder): Product system utilities
        calculate (CalculationManager): Calculation utilities
        results (ResultsAnalyzer): Results analysis utilities
        contributions (ContributionAnalyzer): Contribution analysis
        uncertainty (UncertaintyAnalyzer): Uncertainty analysis
        parameters (ParameterManager): Parameter management
        export (ExportManager): Export utilities
    
    Example:
        >>> client = OLCAClient(port=8080)
        >>> client.test_connection()
        True
        >>> flows = client.search.find_flows(['steel'])
    """
    
    def __init__(self, port: int = 8080, *, read_only: bool = False):
        """
        Initialize the openLCA client.

        Args:
            port: IPC server port (default: 8080)
            read_only: If True, run in safe mode — every database mutation
                (``put``/``delete``/``create_product_system``/...) raises
                :class:`~openlca_ipc.agent.errors.WriteBlocked` instead of
                executing. Reads, searches, and calculations still work.

        Raises:
            ConnectionError: If unable to connect to server
        """
        try:
            raw_client = ipc.Client(port)
            self.port = port
            self.read_only = read_only
            #: Always the unguarded client (internal use / explicit overrides).
            self._raw_client = raw_client
            #: The client handed to managers — guarded when read_only.
            self.client = _ReadOnlyGuard(raw_client) if read_only else raw_client
            mode = " (read-only)" if read_only else ""
            logger.info(f"Connected to openLCA IPC server on port {port}{mode}")

            # Initialize utility modules
            self.search = SearchUtils(self.client)
            self.data = DataBuilder(self.client)
            self.systems = SystemBuilder(self.client)
            self.calculate = CalculationManager(self.client)
            self.results = ResultsAnalyzer(self.client)
            self.contributions = ContributionAnalyzer(self.client)
            self.uncertainty = UncertaintyAnalyzer(self.client)
            self.parameters = ParameterManager(self.client)
            self.export = ExportManager(self.client)
            
        except Exception as e:
            logger.error(f"Failed to connect to openLCA: {e}")
            raise ConnectionError(f"Could not connect to openLCA IPC server on port {port}")
    
    def test_connection(self) -> bool:
        """
        Test if connection to openLCA is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to get Mass property as a connection test
            mass = self.client.get(o.FlowProperty, name="Mass")
            return mass is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        close_fn = getattr(self.client, 'close', None)
        if callable(close_fn):
            close_fn()

