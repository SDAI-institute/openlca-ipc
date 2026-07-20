# ============================================================================
# FILE: olca_utils/results.py
# ============================================================================

"""
Results analysis and retrieval utilities.
"""

import logging
from typing import List, Dict, Optional
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


class ResultsAnalyzer:
    """
    Utilities for analyzing calculation results.
    """
    
    def __init__(self, client: ipc.Client):
        self.client = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _impacts_to_dicts(impact_results) -> List[Dict]:
        """Convert a list of ``o.ImpactValue`` to plain dictionaries."""
        out: List[Dict] = []
        for imp in impact_results:
            amount = imp.amount if imp.amount is not None else 0.0
            cat = imp.impact_category
            out.append({
                'name': cat.name if cat else '',
                'category': cat,
                'amount': amount,
                'unit': getattr(cat, 'ref_unit', ''),
            })
        return out

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_total_impacts(self, result) -> List[Dict]:
        """
        Get all total impact results as dictionaries.

        Args:
            result: Calculation result

        Returns:
            List of impact dictionaries with keys:
                - name: Impact category name
                - amount: Impact value
                - unit: Impact unit

        Example:
            >>> impacts = results.get_total_impacts(result)
            >>> for impact in impacts:
            ...     print(f"{impact['name']}: {impact['amount']}")
        """
        try:
            return self._impacts_to_dicts(result.get_total_impacts())
        except Exception as e:
            logger.error("Error getting impacts: %s", e)
            return []

    def get_normalized_impacts(self, result) -> List[Dict]:
        """
        Get normalized impact results (relative to a normalization set).

        Returns an empty list if the impact method has no normalization set
        or normalization was not computed.

        Args:
            result: Calculation result.

        Returns:
            List of impact dictionaries (same shape as ``get_total_impacts``).
        """
        try:
            return self._impacts_to_dicts(result.get_normalized_impacts())
        except Exception as e:
            logger.error("Error getting normalized impacts: %s", e)
            return []

    def get_weighted_impacts(self, result) -> List[Dict]:
        """
        Get weighted impact results (after normalization + weighting).

        Returns an empty list if the impact method has no weighting set.

        Args:
            result: Calculation result.

        Returns:
            List of impact dictionaries (same shape as ``get_total_impacts``).
        """
        try:
            return self._impacts_to_dicts(result.get_weighted_impacts())
        except Exception as e:
            logger.error("Error getting weighted impacts: %s", e)
            return []

    def get_inventory(self, result, *, direction: str = 'both') -> List[Dict]:
        """
        Get the full life cycle inventory (elementary / environmental flows).

        Uses ``result.get_total_flows()`` which returns ``o.EnviFlowValue``
        items (one per elementary flow with its total amount).

        Args:
            result: Calculation result.
            direction: ``'input'``, ``'output'``, or ``'both'`` (default).

        Returns:
            List of dicts with keys: name, flow (Ref), amount, unit, is_input,
            location. Sorted by absolute amount descending.
        """
        flows: List[Dict] = []
        try:
            for fv in result.get_total_flows():
                ef = fv.envi_flow
                flow_ref = ef.flow if ef else None
                is_input = bool(ef.is_input) if ef else False
                if direction == 'input' and not is_input:
                    continue
                if direction == 'output' and is_input:
                    continue
                loc = ef.location if ef else None
                flows.append({
                    'name': flow_ref.name if flow_ref else '',
                    'flow': flow_ref,
                    'amount': fv.amount if fv.amount is not None else 0.0,
                    'unit': getattr(flow_ref, 'ref_unit', '') if flow_ref else '',
                    'is_input': is_input,
                    'location': getattr(loc, 'name', loc),
                })
            flows.sort(key=lambda f: abs(f['amount']), reverse=True)
        except Exception as e:
            logger.error("Error getting inventory: %s", e)
        return flows

    def get_total_requirements(self, result) -> List[Dict]:
        """
        Get the total requirements (scaled tech-flows) of the product system.

        Uses ``result.get_total_requirements()`` which returns
        ``o.TechFlowValue`` items — the scaled amount of each process needed to
        deliver the functional unit.

        Args:
            result: Calculation result.

        Returns:
            List of dicts with keys: process, provider (Ref), flow, amount.
            Sorted by absolute amount descending.
        """
        reqs: List[Dict] = []
        try:
            for tfv in result.get_total_requirements():
                tf = tfv.tech_flow
                provider = tf.provider if tf else None
                flow = tf.flow if tf else None
                reqs.append({
                    'process': provider.name if provider else '',
                    'provider': provider,
                    'flow': flow.name if flow else '',
                    'amount': tfv.amount if tfv.amount is not None else 0.0,
                })
            reqs.sort(key=lambda r: abs(r['amount']), reverse=True)
        except Exception as e:
            logger.error("Error getting total requirements: %s", e)
        return reqs

    def get_sankey(
        self,
        result,
        impact_category: o.Ref,
        *,
        max_nodes: int = 50,
        min_share: float = 0.0,
    ) -> Dict:
        """
        Get Sankey-graph data for an impact category (viz / MCP friendly).

        Builds an ``o.SankeyRequest`` and calls ``result.get_sankey_graph``.
        The returned ``o.SankeyGraph`` is serialised to a plain dict
        (``nodes``, ``edges``, ``root_index``) ready for visualisation or
        structured agent responses.

        Args:
            result: Calculation result.
            impact_category: Impact category reference to trace.
            max_nodes: Maximum number of nodes in the graph.
            min_share: Minimum share for a node to be included (0 = all).

        Returns:
            Dict form of the Sankey graph, or ``{}`` on error.
        """
        try:
            request = o.SankeyRequest(
                impact_category=impact_category,
                max_nodes=max_nodes,
                min_share=min_share,
            )
            graph = result.get_sankey_graph(request)
            return graph.to_dict() if hasattr(graph, 'to_dict') else graph
        except Exception as e:
            logger.error("Error getting sankey graph: %s", e)
            return {}
