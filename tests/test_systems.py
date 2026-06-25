"""
Tests for SystemBuilder.
"""
import pytest
from unittest.mock import MagicMock, call
import olca_schema as o
from openlca_ipc.systems import SystemBuilder


class TestSystemBuilder:

    def test_initialization(self, mock_ipc_client):
        sb = SystemBuilder(mock_ipc_client)
        assert sb.client is mock_ipc_client

    def test_create_product_system_returns_ref(
        self, mock_ipc_client, sample_process
    ):
        system_ref = o.Ref(id="sys-1", name="My system")
        mock_ipc_client.create_product_system.return_value = system_ref

        sb = SystemBuilder(mock_ipc_client)
        result = sb.create_product_system(sample_process)

        assert result is system_ref
        mock_ipc_client.create_product_system.assert_called_once()

    def test_create_product_system_passes_linking_config(
        self, mock_ipc_client, sample_process
    ):
        """Verify a LinkingConfig is always passed to the underlying client."""
        mock_ipc_client.create_product_system.return_value = o.Ref(id="s1", name="S")

        sb = SystemBuilder(mock_ipc_client)
        sb.create_product_system(sample_process, default_providers='only', preferred_type='UNIT_PROCESS')

        args, kwargs = mock_ipc_client.create_product_system.call_args
        config = args[1] if len(args) > 1 else kwargs.get('config')
        assert isinstance(config, o.LinkingConfig)
        assert config.prefer_unit_processes is True
        assert config.provider_linking == o.ProviderLinking.ONLY_DEFAULTS

    def test_create_product_system_prefer_defaults(
        self, mock_ipc_client, sample_process
    ):
        mock_ipc_client.create_product_system.return_value = o.Ref(id="s1", name="S")

        sb = SystemBuilder(mock_ipc_client)
        sb.create_product_system(sample_process)  # defaults: prefer, LCI_RESULT

        _, kwargs = mock_ipc_client.create_product_system.call_args
        args = mock_ipc_client.create_product_system.call_args[0]
        config = args[1]
        assert config.provider_linking == o.ProviderLinking.PREFER_DEFAULTS
        assert config.prefer_unit_processes is False

    def test_create_product_system_renames_if_name_given(
        self, mock_ipc_client, sample_process
    ):
        system_ref = o.Ref(id="sys-1", name="Auto name")
        full_system = o.ProductSystem()
        full_system.id = "sys-1"
        full_system.name = "Auto name"

        mock_ipc_client.create_product_system.return_value = system_ref
        mock_ipc_client.get.side_effect = None
        mock_ipc_client.get.return_value = full_system

        sb = SystemBuilder(mock_ipc_client)
        sb.create_product_system(sample_process, name="Custom name")

        assert full_system.name == "Custom name"
        mock_ipc_client.put.assert_called_once_with(full_system)

    def test_create_product_system_returns_none_on_error(
        self, mock_ipc_client, sample_process
    ):
        mock_ipc_client.create_product_system.side_effect = RuntimeError("fail")

        sb = SystemBuilder(mock_ipc_client)
        result = sb.create_product_system(sample_process)

        assert result is None
