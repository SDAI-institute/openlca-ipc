"""
Tests for ExportManager.

CSV and JSON paths are pure Python file I/O — tested with tmp_path.
The Excel path delegates to client.excel_export(); that call is mocked.
"""
import csv
import pytest
from unittest.mock import MagicMock
from openlca_ipc.export import ExportManager


SAMPLE_IMPACTS = [
    {'name': 'Global warming', 'amount': 2.5, 'unit': 'kg CO2 eq'},
    {'name': 'Acidification', 'amount': 0.3, 'unit': 'mol H+ eq'},
]

SAMPLE_COMPARISON = {
    'Global warming': {
        'system1': 2.5,
        'system2': 1.8,
        'difference': -0.7,
        'percent_diff': -28.0,
    },
}


class TestExportManager:

    def test_initialization(self, mock_ipc_client):
        em = ExportManager(mock_ipc_client)
        assert em.client is mock_ipc_client

    # ------------------------------------------------------------------
    # export_to_excel
    # ------------------------------------------------------------------

    def test_export_to_excel_creates_file(self, mock_ipc_client, mock_result, tmp_path):
        import olca_schema as o
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(
                impact_category=o.Ref(id="c1", name="Global warming"),
                amount=2.5,
            ),
        ]
        filepath = tmp_path / "out.xlsx"
        em = ExportManager(mock_ipc_client)
        success = em.export_to_excel(mock_result, str(filepath))

        assert success is True
        assert filepath.exists()

    def test_export_to_excel_content(self, mock_ipc_client, mock_result, tmp_path):
        import openpyxl
        import olca_schema as o
        mock_result.get_total_impacts.return_value = [
            o.ImpactValue(
                impact_category=o.Ref(id="c1", name="Global warming"),
                amount=2.5,
            ),
        ]
        filepath = tmp_path / "out.xlsx"
        em = ExportManager(mock_ipc_client)
        em.export_to_excel(mock_result, str(filepath))

        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        assert rows[0] == ("Impact Category", "Amount", "Unit")
        assert rows[1][0] == "Global warming"
        assert rows[1][1] == pytest.approx(2.5)

    def test_export_to_excel_returns_false_on_error(
        self, mock_ipc_client, mock_result, tmp_path
    ):
        mock_result.get_total_impacts.side_effect = RuntimeError("result error")
        em = ExportManager(mock_ipc_client)
        assert em.export_to_excel(mock_result, str(tmp_path / "out.xlsx")) is False

    # ------------------------------------------------------------------
    # export_impacts_to_csv
    # ------------------------------------------------------------------

    def test_export_impacts_to_csv_creates_file(self, mock_ipc_client, tmp_path):
        filepath = tmp_path / "impacts.csv"
        em = ExportManager(mock_ipc_client)
        success = em.export_impacts_to_csv(SAMPLE_IMPACTS, str(filepath))

        assert success is True
        assert filepath.exists()

    def test_export_impacts_to_csv_content(self, mock_ipc_client, tmp_path):
        filepath = tmp_path / "impacts.csv"
        em = ExportManager(mock_ipc_client)
        em.export_impacts_to_csv(SAMPLE_IMPACTS, str(filepath))

        with open(filepath, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]['name'] == 'Global warming'
        assert float(rows[0]['amount']) == pytest.approx(2.5)
        assert rows[0]['unit'] == 'kg CO2 eq'

    def test_export_impacts_to_csv_returns_false_for_empty(
        self, mock_ipc_client, tmp_path
    ):
        em = ExportManager(mock_ipc_client)
        result = em.export_impacts_to_csv([], str(tmp_path / "empty.csv"))
        assert result is False

    def test_export_impacts_to_csv_error_returns_false(
        self, mock_ipc_client
    ):
        em = ExportManager(mock_ipc_client)
        # Pass an unwritable path on all platforms
        result = em.export_impacts_to_csv(SAMPLE_IMPACTS, "/no/such/dir/out.csv")
        assert result is False

    # ------------------------------------------------------------------
    # export_comparison_to_csv
    # ------------------------------------------------------------------

    def test_export_comparison_to_csv_creates_file(self, mock_ipc_client, tmp_path):
        filepath = tmp_path / "compare.csv"
        em = ExportManager(mock_ipc_client)
        success = em.export_comparison_to_csv(SAMPLE_COMPARISON, str(filepath))

        assert success is True
        assert filepath.exists()

    def test_export_comparison_to_csv_content(self, mock_ipc_client, tmp_path):
        filepath = tmp_path / "compare.csv"
        em = ExportManager(mock_ipc_client)
        em.export_comparison_to_csv(SAMPLE_COMPARISON, str(filepath))

        with open(filepath, encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        header = rows[0]
        assert 'Impact Category' in header
        assert 'System 1' in header
        assert 'System 2' in header
        assert len(rows) == 2  # header + 1 data row

    def test_export_comparison_returns_false_on_error(self, mock_ipc_client):
        em = ExportManager(mock_ipc_client)
        result = em.export_comparison_to_csv(
            SAMPLE_COMPARISON, "/no/such/dir/out.csv"
        )
        assert result is False
