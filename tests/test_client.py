"""
Tests for OLCAClient class.

The client module imports olca_ipc as ``ipc`` (``import olca_ipc as ipc``),
so the patch target is ``openlca_ipc.client.ipc.Client``.
"""
import pytest
from unittest.mock import patch, MagicMock
from openlca_ipc import OLCAClient


class TestOLCAClient:
    """Test suite for OLCAClient."""

    def test_client_initialization(self):
        """Test client can be initialized with default parameters."""
        with patch('openlca_ipc.client.ipc.Client'):
            client = OLCAClient(port=8080)
            assert client is not None
            assert hasattr(client, 'search')
            assert hasattr(client, 'data')
            assert hasattr(client, 'systems')
            assert hasattr(client, 'calculate')
            assert hasattr(client, 'results')
            assert hasattr(client, 'contributions')
            assert hasattr(client, 'uncertainty')
            assert hasattr(client, 'parameters')
            assert hasattr(client, 'export')

    def test_client_has_utility_modules(self):
        """Test client has all expected utility modules."""
        with patch('openlca_ipc.client.ipc.Client'):
            client = OLCAClient(port=8080)

            from openlca_ipc.search import SearchUtils
            from openlca_ipc.data import DataBuilder
            from openlca_ipc.systems import SystemBuilder
            from openlca_ipc.calculations import CalculationManager
            from openlca_ipc.results import ResultsAnalyzer
            from openlca_ipc.contributions import ContributionAnalyzer
            from openlca_ipc.uncertainty import UncertaintyAnalyzer
            from openlca_ipc.parameters import ParameterManager
            from openlca_ipc.export import ExportManager

            assert isinstance(client.search, SearchUtils)
            assert isinstance(client.data, DataBuilder)
            assert isinstance(client.systems, SystemBuilder)
            assert isinstance(client.calculate, CalculationManager)
            assert isinstance(client.results, ResultsAnalyzer)
            assert isinstance(client.contributions, ContributionAnalyzer)
            assert isinstance(client.uncertainty, UncertaintyAnalyzer)
            assert isinstance(client.parameters, ParameterManager)
            assert isinstance(client.export, ExportManager)

    def test_context_manager(self):
        """Test client works as context manager."""
        with patch('openlca_ipc.client.ipc.Client'):
            with OLCAClient(port=8080) as client:
                assert client is not None
                assert hasattr(client, 'search')

    def test_context_manager_no_close_method(self):
        """__exit__ must not raise even when the ipc.Client has no close()."""
        with patch('openlca_ipc.client.ipc.Client') as mock_class:
            # Simulate a client instance that has no close() attribute
            mock_instance = MagicMock(spec=[
                'get', 'get_descriptors', 'put', 'calculate',
                'get_providers', 'create_product_system', 'simulate',
                'update', 'delete',
            ])
            mock_instance.get.return_value = None
            mock_class.return_value = mock_instance

            # Must not raise AttributeError on exit
            with OLCAClient(port=8080):
                pass

    def test_client_custom_port(self):
        """Test client accepts and stores a custom port."""
        with patch('openlca_ipc.client.ipc.Client'):
            client = OLCAClient(port=9090)
            assert client is not None
            assert client.port == 9090

    def test_connection_failure_raises(self):
        """Test a failed connection raises ConnectionError."""
        with patch('openlca_ipc.client.ipc.Client', side_effect=Exception("boom")):
            with pytest.raises(ConnectionError):
                OLCAClient(port=8080)

    def test_test_connection_success(self):
        """Test connection test returns True when the Mass property resolves."""
        with patch('openlca_ipc.client.ipc.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.return_value = MagicMock()  # non-None Mass property
            mock_client_class.return_value = mock_client

            client = OLCAClient(port=8080)
            assert client.test_connection() is True

    def test_test_connection_failure(self):
        """Test connection test returns False when the Mass property is missing."""
        with patch('openlca_ipc.client.ipc.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_client.get.return_value = None
            mock_client_class.return_value = mock_client

            client = OLCAClient(port=8080)
            assert client.test_connection() is False
