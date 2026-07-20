# ============================================================================
# FILE: olca_utils/export.py
# ============================================================================

"""
Export utilities for results and data.
"""

import logging
import csv
import json
from pathlib import Path
from typing import List, Dict
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


class ExportManager:
    """
    Utilities for exporting results and data.
    
    Supports export to Excel, CSV, JSON, and other formats.
    """
    
    def __init__(self, client: ipc.Client):
        self.client = client

    @staticmethod
    def _flatten_row(row: Dict) -> Dict:
        """Coerce a result dict into CSV-writable scalars.

        Nested objects (e.g. a ``category`` Ref) are reduced to their ``name``
        (or ``str``) so ``csv`` does not choke on them.
        """
        flat = {}
        for k, v in row.items():
            if v is None or isinstance(v, (str, int, float, bool)):
                flat[k] = v
            else:
                flat[k] = getattr(v, "name", None) or str(v)
        return flat

    def export_to_excel(
        self,
        result,
        filepath: str
    ) -> bool:
        """
        Export total impact results to an Excel workbook.

        Requires the ``openpyxl`` package (``pip install openlca-ipc[export]``).

        Args:
            result: Calculation result (olca_ipc Result object).
            filepath: Output .xlsx file path.

        Returns:
            True if successful, False otherwise.

        Example:
            >>> export.export_to_excel(result, 'lca_results.xlsx')
        """
        try:
            import openpyxl  # optional dependency
        except ImportError:
            logger.error(
                "Excel export requires openpyxl: pip install 'openlca-ipc[export]'"
            )
            return False

        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Impact Assessment"
            ws.append(["Impact Category", "Amount", "Unit"])

            for iv in result.get_total_impacts():
                cat = iv.impact_category
                name = cat.name if cat else ''
                unit = getattr(cat, 'ref_unit', '') or ''
                amount = iv.amount if iv.amount is not None else 0.0
                ws.append([name, amount, unit])

            wb.save(filepath)
            logger.info("Exported results to %s", filepath)
            return True

        except Exception as e:
            logger.error("Excel export failed: %s", e)
            return False
    
    def export_impacts_to_csv(
        self,
        impacts: List[Dict],
        filepath: str
    ) -> bool:
        """
        Export impact results to CSV.
        
        Args:
            impacts: List of impact dictionaries
            filepath: Output CSV file path
        
        Returns:
            True if successful
        
        Example:
            >>> impacts = results.get_total_impacts(result)
            >>> export.export_impacts_to_csv(impacts, 'impacts.csv')
        """
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not impacts:
                    return False

                # Build the header from the preferred columns that are actually
                # present, then append any other keys. ``extrasaction='ignore'``
                # keeps unexpected keys from crashing the writer, and each row is
                # flattened so nested objects (e.g. a ``category`` Ref) become
                # plain strings instead of raising.
                preferred = ['name', 'category', 'category_id', 'amount', 'unit']
                present = set().union(*(row.keys() for row in impacts))
                fieldnames = [c for c in preferred if c in present]
                fieldnames += [k for k in present if k not in fieldnames]

                rows = [self._flatten_row(row) for row in impacts]
                writer = csv.DictWriter(
                    f, fieldnames=fieldnames, extrasaction='ignore'
                )
                writer.writeheader()
                writer.writerows(rows)

            logger.info(f"Exported {len(impacts)} impacts to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def export_comparison_to_csv(
        self,
        comparison_data: Dict[str, Dict],
        filepath: str
    ) -> bool:
        """
        Export comparison results to CSV.
        
        Args:
            comparison_data: Comparison dictionary
            filepath: Output CSV file path
        
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Impact Category', 'System 1', 'System 2', 'Difference', '% Difference'])
                
                for impact, data in comparison_data.items():
                    writer.writerow([
                        impact,
                        f"{data.get('system1', 0):.4e}",
                        f"{data.get('system2', 0):.4e}",
                        f"{data.get('difference', 0):.4e}",
                        f"{data.get('percent_diff', 0):.2f}%"
                    ])
            
            logger.info(f"Exported comparison to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Comparison export failed: {e}")
            return False
