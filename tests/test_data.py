"""
Tests for DataBuilder class.

Signatures under test:
    create_product_flow(name, description="") -> o.Flow
    create_exchange(flow, amount, is_input, is_quantitative_reference=False,
                    provider=None) -> o.Exchange
    create_process(name, description="", exchanges=None) -> o.Process
"""
import pytest
from unittest.mock import MagicMock
import olca_schema as o
from openlca_ipc.data import DataBuilder


class TestDataBuilder:
    """Test suite for DataBuilder."""

    def test_data_builder_initialization(self, mock_ipc_client):
        """Test DataBuilder can be initialized."""
        builder = DataBuilder(mock_ipc_client)
        assert builder is not None
        assert builder.client == mock_ipc_client

    def test_mass_property_cached(self, mock_ipc_client):
        """Mass property is resolved from the client and cached."""
        builder = DataBuilder(mock_ipc_client)
        prop = builder.mass_property
        assert prop.name == "Mass"
        # Second access should reuse the cache, not call get again.
        calls_before = mock_ipc_client.get.call_count
        _ = builder.mass_property
        assert mock_ipc_client.get.call_count == calls_before

    def test_kg_unit(self, mock_ipc_client):
        """kg unit is resolved from the mass property's unit group."""
        builder = DataBuilder(mock_ipc_client)
        assert builder.kg_unit.name == "kg"

    def test_create_product_flow(self, mock_ipc_client):
        """create_product_flow creates a product flow and persists it."""
        builder = DataBuilder(mock_ipc_client)
        flow = builder.create_product_flow(name="Test Product", description="1mm")

        assert isinstance(flow, o.Flow)
        assert flow.name == "Test Product"
        assert flow.flow_type == o.FlowType.PRODUCT_FLOW
        assert flow.id  # a uuid was assigned
        assert flow.flow_properties and flow.flow_properties[0].is_ref_flow_property
        assert mock_ipc_client.put.called

    def test_create_exchange(self, mock_ipc_client, sample_flow):
        """create_exchange builds an exchange with the right amount/direction."""
        builder = DataBuilder(mock_ipc_client)
        exchange = builder.create_exchange(
            flow=sample_flow,
            amount=1.0,
            is_input=True,
            is_quantitative_reference=False,
        )

        assert isinstance(exchange, o.Exchange)
        assert exchange.amount == 1.0
        assert exchange.is_input is True
        assert exchange.is_quantitative_reference is False
        assert exchange.flow.id == sample_flow.id

    def test_create_exchange_with_provider(self, mock_ipc_client, sample_flow, sample_process):
        """create_exchange links a default provider when one is supplied."""
        builder = DataBuilder(mock_ipc_client)
        exchange = builder.create_exchange(
            flow=sample_flow,
            amount=2.0,
            is_input=True,
            provider=sample_process,
        )

        assert exchange.amount == 2.0
        assert exchange.default_provider is not None
        assert exchange.default_provider.id == sample_process.id

    def test_create_exchange_rejects_bad_flow(self, mock_ipc_client):
        """create_exchange raises TypeError for an unsupported flow type."""
        builder = DataBuilder(mock_ipc_client)
        with pytest.raises(TypeError):
            builder.create_exchange(flow="not-a-flow", amount=1.0, is_input=True)

    def test_create_process(self, mock_ipc_client):
        """create_process creates a process with exchanges and persists it."""
        exchanges = [
            o.Exchange(amount=1.0, is_input=False, is_quantitative_reference=True),
        ]

        builder = DataBuilder(mock_ipc_client)
        process = builder.create_process(name="Test Process", exchanges=exchanges)

        assert isinstance(process, o.Process)
        assert process.name == "Test Process"
        assert process.process_type == o.ProcessType.UNIT_PROCESS
        assert process.exchanges[0].internal_id == 1
        assert process.last_internal_id == 1
        assert mock_ipc_client.put.called

    def test_create_process_warns_on_missing_qref(self, mock_ipc_client, caplog):
        """A process without exactly one quantitative reference logs a warning."""
        exchanges = [
            o.Exchange(amount=1.0, is_input=True, is_quantitative_reference=False),
        ]

        builder = DataBuilder(mock_ipc_client)
        with caplog.at_level("WARNING"):
            process = builder.create_process(name="No Qref", exchanges=exchanges)

        assert isinstance(process, o.Process)
        assert any("qref" in rec.message.lower() for rec in caplog.records)
