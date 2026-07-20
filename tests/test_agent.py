"""
Tests for the agent layer (openlca_ipc.agent) and safe-mode client guard.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
import olca_schema as o
import olca_ipc as ipc

from openlca_ipc.agent import (
    OLCAError,
    WriteBlocked,
    ImpactMethodNotFound,
    EntitySummary,
    ResultSummary,
    CalculationContext,
    health_check,
)
from openlca_ipc.client import OLCAClient, _ReadOnlyGuard


# ---------------------------------------------------------------------------
# Structured errors
# ---------------------------------------------------------------------------

class TestErrors:

    def test_subclass_envelope(self):
        e = ImpactMethodNotFound(message="No impact method matched 'EF 3.1'.")
        d = e.to_dict()
        assert d["is_error"] is True
        assert d["error_code"] == "IMPACT_METHOD_NOT_FOUND"
        assert d["recoverable"] is True
        assert "search_impact_methods" in d["suggested_next_actions"]

    def test_base_custom_fields(self):
        e = OLCAError("X_CODE", "boom", recoverable=False, suggested_next_actions=["a"])
        assert e.to_dict() == {
            "is_error": True,
            "error_code": "X_CODE",
            "message": "boom",
            "recoverable": False,
            "suggested_next_actions": ["a"],
        }

    def test_write_blocked_names_operation(self):
        e = WriteBlocked(operation="put")
        assert e.error_code == "WRITE_BLOCKED"
        assert "put" in e.message
        assert e.operation == "put"
        assert isinstance(e, OLCAError)


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------

class TestEntitySummary:

    def test_from_ref(self):
        s = EntitySummary.from_ref(o.Ref(id="f1", name="Steel"), type_name="Flow")
        d = s.to_dict()
        assert d == {"id": "f1", "name": "Steel", "type": "Flow", "category": None}

    def test_to_json_roundtrip(self):
        s = EntitySummary(id="x", name="Y", type="Flow")
        assert json.loads(s.to_json())["name"] == "Y"


class TestResultSummary:

    def test_ranks_by_abs_amount_and_truncates(self):
        impacts = [
            {"name": "A", "amount": 1.0, "unit": "u"},
            {"name": "B", "amount": 5.0, "unit": "u"},
            {"name": "C", "amount": -9.0, "unit": "u"},
        ]
        rs = ResultSummary.from_impacts(
            impacts, top_n=2, impact_method=o.Ref(id="m", name="EF 3.1")
        )
        cats = [i["category"] for i in rs.top_impacts]
        assert cats == ["C", "B"]  # by absolute magnitude
        assert rs.impact_method == {"id": "m", "name": "EF 3.1"}
        assert rs.next_actions  # defaults populated

    def test_json_shape_matches_contract(self):
        rs = ResultSummary.from_impacts(
            [{"name": "A", "amount": 2.0, "unit": "kg"}],
            result_id="res_1",
            database="demo",
            product_system=o.Ref(id="s", name="Sys"),
            functional_unit={"amount": 1, "unit": "L"},
        )
        d = json.loads(rs.to_json())
        assert d["result_id"] == "res_1"
        assert d["database"] == "demo"
        assert d["product_system"] == {"id": "s", "name": "Sys"}
        assert set(d) >= {
            "result_id", "database", "product_system", "functional_unit",
            "impact_method", "top_impacts", "next_actions", "warnings",
        }

    def test_dict_passthrough_for_method(self):
        rs = ResultSummary.from_impacts([], impact_method={"id": "m", "name": "EF"})
        assert rs.impact_method == {"id": "m", "name": "EF"}


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestCalculationContext:

    def test_capture_autofills(self):
        ctx = CalculationContext.capture(
            database="demo",
            server_port=8080,
            product_system=o.Ref(id="s", name="Sys"),
            impact_method=o.Ref(id="m", name="EF"),
            functional_unit={"amount": 1, "unit": "kg"},
        )
        d = ctx.to_dict()
        assert d["result_id"].startswith("res_")
        assert d["timestamp"]
        assert d["olca_ipc_version"]  # installed in the test env
        assert d["product_system"] == {"id": "s", "name": "Sys"}
        assert d["database"] == "demo"
        assert d["server_port"] == 8080

    def test_explicit_result_id(self):
        ctx = CalculationContext.capture(result_id="res_fixed")
        assert ctx.result_id == "res_fixed"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:

    def test_unwraps_olca_client_and_counts(self, mock_ipc_client):
        mock_ipc_client.get_descriptors.return_value = [o.Ref(id="1", name="x")]
        wrapper = MagicMock()  # stand-in for OLCAClient (has .client and .port)
        wrapper.client = mock_ipc_client
        wrapper.port = 8080

        report = health_check(wrapper)
        assert report["connected"] is True
        assert report["server_port"] == 8080
        assert report["counts"]["processes"] == 1
        assert report["counts"]["product_systems"] == 1

    def test_accepts_raw_client_without_counts(self, mock_ipc_client):
        report = health_check(mock_ipc_client, count_entities=False)
        assert report["connected"] is True
        assert report["counts"] == {}

    def test_connection_failure_reported(self):
        bad = MagicMock(spec=ipc.Client)
        bad.get.side_effect = RuntimeError("no server")
        report = health_check(bad)
        assert report["connected"] is False
        assert report["errors"]


# ---------------------------------------------------------------------------
# Safe mode
# ---------------------------------------------------------------------------

class TestSafeMode:

    def test_guard_blocks_writes(self, mock_ipc_client):
        guard = _ReadOnlyGuard(mock_ipc_client)
        for op, call in [
            ("put", lambda: guard.put(o.Flow())),
            ("delete", lambda: guard.delete(o.Flow())),
            ("create_product_system", lambda: guard.create_product_system(o.Process())),
        ]:
            with pytest.raises(WriteBlocked):
                call()

    def test_guard_allows_reads(self, mock_ipc_client):
        guard = _ReadOnlyGuard(mock_ipc_client)
        assert guard.get(o.FlowProperty, name="Mass") is not None
        assert guard.get_descriptors(o.Process) == []

    def test_client_read_only_blocks_write_allows_read(self, mock_ipc_client):
        with patch("openlca_ipc.client.ipc.Client", return_value=mock_ipc_client):
            c = OLCAClient(read_only=True)
            assert c.read_only is True
            with pytest.raises(WriteBlocked):
                c.client.put(o.Flow())
            assert c.test_connection() is True  # reads still work

    def test_client_default_allows_writes(self, mock_ipc_client):
        with patch("openlca_ipc.client.ipc.Client", return_value=mock_ipc_client):
            c = OLCAClient()
            assert c.read_only is False
            c.client.put(o.Flow())  # delegates to the mock, no raise
            mock_ipc_client.put.assert_called_once()
