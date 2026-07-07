"""
Tests for SearchUtils class.
"""
import types
import pytest
from unittest.mock import MagicMock
import olca_schema as o
from openlca_ipc.search import SearchUtils


class TestSearchUtils:
    """Test suite for SearchUtils."""

    def test_search_utils_initialization(self, mock_ipc_client):
        """Test SearchUtils can be initialized."""
        search = SearchUtils(mock_ipc_client)
        assert search is not None
        assert search.client == mock_ipc_client

    def test_find_flows_with_results(self, mock_ipc_client):
        """Test find_flows returns flows matching all keywords."""
        flow_refs = [
            o.Ref(id="f1", name="Steel plate"),
            o.Ref(id="f2", name="Steel rod"),
        ]
        mock_ipc_client.get_descriptors.return_value = flow_refs

        search = SearchUtils(mock_ipc_client)
        results = search.find_flows(['steel'], max_results=5)

        assert len(results) == 2
        assert results[0].name == "Steel plate"

    def test_find_flows_all_keywords_must_match(self, mock_ipc_client):
        """Only flows containing every keyword are returned."""
        flow_refs = [
            o.Ref(id="f1", name="Steel plate"),
            o.Ref(id="f2", name="Aluminium plate"),
        ]
        mock_ipc_client.get_descriptors.return_value = flow_refs

        search = SearchUtils(mock_ipc_client)
        results = search.find_flows(['steel', 'plate'])

        assert len(results) == 1
        assert results[0].name == "Steel plate"

    def test_find_flows_respects_max_results(self, mock_ipc_client):
        """find_flows stops at max_results."""
        flow_refs = [o.Ref(id=f"f{i}", name=f"Steel {i}") for i in range(10)]
        mock_ipc_client.get_descriptors.return_value = flow_refs

        search = SearchUtils(mock_ipc_client)
        results = search.find_flows(['steel'], max_results=3)

        assert len(results) == 3

    def test_find_flow_single_result(self, mock_ipc_client):
        """Test find_flow returns the first matching flow."""
        mock_ipc_client.get_descriptors.return_value = [o.Ref(id="f1", name="Steel plate")]

        search = SearchUtils(mock_ipc_client)
        result = search.find_flow(['steel'])

        assert result is not None
        assert result.name == "Steel plate"

    def test_find_flow_no_results(self, mock_ipc_client):
        """Test find_flow returns None when nothing matches."""
        mock_ipc_client.get_descriptors.return_value = []

        search = SearchUtils(mock_ipc_client)
        assert search.find_flow(['nonexistent']) is None

    def test_find_processes(self, mock_ipc_client):
        """Test find_processes returns matching processes."""
        process_refs = [
            o.Ref(id="p1", name="Steel production"),
            o.Ref(id="p2", name="Steel processing"),
        ]
        mock_ipc_client.get_descriptors.return_value = process_refs

        search = SearchUtils(mock_ipc_client)
        results = search.find_processes(['steel'], max_results=5)

        assert len(results) == 2
        assert results[0].name == "Steel production"

    def test_find_impact_method(self, mock_ipc_client):
        """Test find_impact_method resolves a full method by keyword."""
        method_ref = o.Ref(id="m1", name="TRACI 2.1")
        mock_ipc_client.get_descriptors.return_value = [method_ref]

        full_method = o.ImpactMethod()
        full_method.id = "m1"
        full_method.name = "TRACI 2.1"
        # Override the conftest side effect for this call.
        mock_ipc_client.get.side_effect = None
        mock_ipc_client.get.return_value = full_method

        search = SearchUtils(mock_ipc_client)
        result = search.find_impact_method(['TRACI'])

        assert result is not None
        assert result.name == "TRACI 2.1"

    def test_find_impact_method_no_match(self, mock_ipc_client):
        """find_impact_method returns None when no descriptor matches."""
        mock_ipc_client.get_descriptors.return_value = [o.Ref(id="m1", name="ReCiPe")]

        search = SearchUtils(mock_ipc_client)
        assert search.find_impact_method(['TRACI']) is None

    def test_find_impact_method_version_normalization(self, mock_ipc_client):
        """v0.4.1: 'EF v3.1' resolves to 'EF 3.1 Method (adapted)'."""
        ef = o.Ref(id="ef31", name="EF 3.1 Method (adapted)")
        mock_ipc_client.get_descriptors.return_value = [
            o.Ref(id="ef30", name="EF 3.0 Method (adapted)"),
            ef,
            o.Ref(id="traci", name="TRACI 2.1"),
        ]
        full = o.ImpactMethod(id="ef31", name="EF 3.1 Method (adapted)")
        mock_ipc_client.get.side_effect = None
        mock_ipc_client.get.return_value = full

        search = SearchUtils(mock_ipc_client)
        result = search.find_impact_method(['EF v3.1'])
        assert result is not None and result.id == "ef31"

    def test_find_impact_methods_ranked(self, mock_ipc_client):
        """find_impact_methods returns ranked candidates, best first."""
        mock_ipc_client.get_descriptors.return_value = [
            o.Ref(id="ef30", name="EF 3.0 Method (adapted)"),
            o.Ref(id="ef31", name="EF 3.1 Method (adapted)"),
            o.Ref(id="traci", name="TRACI 2.1"),
        ]
        search = SearchUtils(mock_ipc_client)
        hits = search.find_impact_methods(['EF v3.1'])
        assert hits[0].id == "ef31"  # full 'ef'+'3.1' match ranks first
        assert all(h.id != "traci" for h in hits)

    def test_find_providers(self, mock_ipc_client, sample_flow):
        """find_providers extracts provider refs from TechFlow objects."""
        provider_ref = o.Ref(id="p1", name="Steel producer")
        tech_flow = types.SimpleNamespace(provider=provider_ref)
        mock_ipc_client.get_providers.return_value = [tech_flow]

        search = SearchUtils(mock_ipc_client)
        providers = search.find_providers(sample_flow)

        assert len(providers) == 1
        assert providers[0].name == "Steel producer"

    def test_find_best_provider(self, mock_ipc_client, sample_flow):
        """find_best_provider returns the first provider."""
        provider_ref = o.Ref(id="p1", name="Steel producer")
        tech_flow = types.SimpleNamespace(provider=provider_ref)
        mock_ipc_client.get_providers.return_value = [tech_flow]

        search = SearchUtils(mock_ipc_client)
        provider = search.find_best_provider(sample_flow)

        assert provider is not None
        assert provider.name == "Steel producer"

    def test_find_best_provider_none(self, mock_ipc_client, sample_flow):
        """find_best_provider returns None when there are no providers."""
        mock_ipc_client.get_providers.return_value = []

        search = SearchUtils(mock_ipc_client)
        assert search.find_best_provider(sample_flow) is None
