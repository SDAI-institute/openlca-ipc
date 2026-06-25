"""
Tests for CalculationManager class.

Signatures under test:
    simple_calculation(system, impact_method=None, amount=1.0)
    contribution_analysis(system, impact_method, amount=1.0)
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o
from openlca_ipc.calculations import CalculationManager


class TestCalculationManager:
    """Test suite for CalculationManager."""

    def test_calculation_manager_initialization(self, mock_ipc_client):
        """Test CalculationManager can be initialized."""
        calc = CalculationManager(mock_ipc_client)
        assert calc is not None
        assert calc.client == mock_ipc_client

    def test_simple_calculation_setup(self, mock_ipc_client, sample_product_system, sample_impact_method):
        """simple_calculation builds a setup and waits for the result."""
        mock_result = MagicMock()
        mock_ipc_client.calculate.return_value = mock_result

        calc = CalculationManager(mock_ipc_client)
        result = calc.simple_calculation(
            system=sample_product_system,
            impact_method=sample_impact_method,
        )

        assert result is mock_result
        assert mock_ipc_client.calculate.called
        mock_result.wait_until_ready.assert_called_once()

        setup = mock_ipc_client.calculate.call_args[0][0]
        assert isinstance(setup, o.CalculationSetup)
        assert setup.target == sample_product_system
        assert setup.amount == 1.0
        assert setup.impact_method is not None

    def test_simple_calculation_without_method(self, mock_ipc_client, sample_product_system):
        """simple_calculation works without an impact method (inventory only)."""
        mock_result = MagicMock()
        mock_ipc_client.calculate.return_value = mock_result

        calc = CalculationManager(mock_ipc_client)
        result = calc.simple_calculation(system=sample_product_system, amount=2.0)

        assert result is mock_result
        setup = mock_ipc_client.calculate.call_args[0][0]
        assert setup.amount == 2.0
        assert setup.impact_method is None

    def test_contribution_analysis_setup(self, mock_ipc_client, sample_product_system, sample_impact_method):
        """contribution_analysis builds a setup with the impact method set."""
        mock_result = MagicMock()
        mock_ipc_client.calculate.return_value = mock_result

        calc = CalculationManager(mock_ipc_client)
        result = calc.contribution_analysis(
            system=sample_product_system,
            impact_method=sample_impact_method,
        )

        assert result is mock_result
        assert mock_ipc_client.calculate.called
        mock_result.wait_until_ready.assert_called_once()

        setup = mock_ipc_client.calculate.call_args[0][0]
        assert isinstance(setup, o.CalculationSetup)
        assert setup.impact_method is not None
