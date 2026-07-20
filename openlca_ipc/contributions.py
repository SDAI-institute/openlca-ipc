# ============================================================================
# FILE: olca_utils/contributions.py
# ============================================================================

"""
Contribution analysis utilities.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


@dataclass
class ContributionItem:
    """
    Represents a contribution to an impact.

    Attributes:
        name: Contributor name (process, flow, or location)
        amount: Absolute contribution value
        share: Relative share (0-1); NaN when total is zero
        ref: Reference to the contributor (process Ref or flow Ref)
    """
    name: str
    amount: float
    share: float
    ref: Optional[o.Ref] = None


@dataclass
class TreeNode:
    """
    A node in an upstream contribution tree.

    Attributes:
        name: Provider (process) name for this node.
        amount: Total upstream result accumulated at this node.
        direct: Direct (own) contribution of this node, excluding upstream.
        share: ``amount`` as a fraction of the category total; NaN if total is 0.
        ref: Provider process reference for this node, if available.
        children: Upstream child nodes, sorted by absolute amount descending.
    """
    name: str
    amount: float
    direct: float
    share: float
    ref: Optional[o.Ref] = None
    children: List['TreeNode'] = field(default_factory=list)


class ContributionAnalyzer:
    """
    Utilities for detailed contribution analysis.

    Provides methods to identify top contributors to impacts at
    process and flow levels using the Result object API introduced in
    olca-ipc 2.x (get_impact_contributions_of / get_flow_impacts_of).
    """

    def __init__(self, client: ipc.Client):
        self.client = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _total_for_category(result, impact_category: o.Ref) -> float:
        """Return the total impact amount for *impact_category*, or 0."""
        try:
            for iv in result.get_total_impacts():
                cat = iv.impact_category
                if cat and cat.id == impact_category.id:
                    return iv.amount or 0.0
        except Exception:
            pass
        return 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_process_contributions(
        self,
        result,
        impact_category: o.Ref,
        min_share: float = 0.01,
    ) -> List[ContributionItem]:
        """
        Get process (tech-flow) contributions to an impact category.

        Uses ``result.get_impact_contributions_of(impact_category)`` which
        returns a list of ``o.TechFlowValue`` items — one per process/
        tech-flow that contributes to the given category.

        Args:
            result: Calculation result (olca_ipc Result object).
            impact_category: Impact category reference (o.Ref).
            min_share: Minimum absolute share to include (default 1 %).

        Returns:
            List of ContributionItem, sorted by absolute amount descending.
        """
        try:
            raw = result.get_impact_contributions_of(impact_category)

            total = self._total_for_category(result, impact_category)

            items: List[ContributionItem] = []
            for tfv in raw:
                amount = tfv.amount or 0.0
                share = (amount / total) if total else float('nan')
                if abs(share) < min_share and total:
                    continue
                tf = tfv.tech_flow
                provider = tf.provider if tf else None
                name = provider.name if provider else str(tfv)
                items.append(ContributionItem(
                    name=name,
                    amount=amount,
                    share=share,
                    ref=provider,
                ))

            items.sort(key=lambda x: abs(x.amount), reverse=True)
            return items

        except Exception as e:
            logger.error("Error getting process contributions: %s", e)
            return []

    def get_flow_contributions(
        self,
        result,
        impact_category: o.Ref,
        min_share: float = 0.01,
    ) -> List[ContributionItem]:
        """
        Get elementary-flow contributions to an impact category.

        Uses ``result.get_flow_impacts_of(impact_category)`` which returns a
        list of ``o.EnviFlowValue`` items — one per elementary flow.

        Args:
            result: Calculation result.
            impact_category: Impact category reference.
            min_share: Minimum absolute share to include (default 1 %).

        Returns:
            List of ContributionItem, sorted by absolute amount descending.
        """
        try:
            raw = result.get_flow_impacts_of(impact_category)

            total = self._total_for_category(result, impact_category)

            items: List[ContributionItem] = []
            for efv in raw:
                amount = efv.amount or 0.0
                share = (amount / total) if total else float('nan')
                if abs(share) < min_share and total:
                    continue
                ef = efv.envi_flow
                flow_ref = ef.flow if ef else None
                name = flow_ref.name if flow_ref else str(efv)
                items.append(ContributionItem(
                    name=name,
                    amount=amount,
                    share=share,
                    ref=flow_ref,
                ))

            items.sort(key=lambda x: abs(x.amount), reverse=True)
            return items

        except Exception as e:
            logger.error("Error getting flow contributions: %s", e)
            return []

    def get_contribution_tree(
        self,
        result,
        impact_category: o.Ref,
        *,
        max_depth: int = 3,
        min_share: float = 0.01,
    ) -> List[TreeNode]:
        """
        Build an upstream contribution (hotspot) tree for an impact category.

        Walks ``result.get_upstream_impacts_of(impact_category, path)``, where
        *path* is the list of ``o.TechFlow`` objects from the root down to the
        current node. Starting from an empty path, each node is expanded by
        appending its own tech-flow to the path until ``max_depth`` is reached
        or a branch falls below ``min_share`` of the category total.

        Each upstream RPC call expands one node, so depth and ``min_share``
        bound the request count (and prevent runaway recursion on cyclic
        product systems).

        Args:
            result: Calculation result (olca_ipc Result object).
            impact_category: Impact category reference (o.Ref).
            max_depth: Maximum tree depth (root level = 1).
            min_share: Minimum absolute share to keep a branch (default 1 %).

        Returns:
            Top-level TreeNode list, each with nested ``children``, sorted by
            absolute amount descending. Empty list on error.
        """
        total = self._total_for_category(result, impact_category)

        def expand(path: List[o.TechFlow], depth: int) -> List[TreeNode]:
            nodes = result.get_upstream_impacts_of(impact_category, path)
            out: List[TreeNode] = []
            for n in nodes:
                amount = n.result or 0.0
                share = (amount / total) if total else float('nan')
                if total and abs(share) < min_share:
                    continue
                tf = n.tech_flow
                provider = tf.provider if tf else None
                name = provider.name if provider else str(n)
                node = TreeNode(
                    name=name,
                    amount=amount,
                    direct=n.direct_contribution or 0.0,
                    share=share,
                    ref=provider,
                )
                if depth < max_depth and tf is not None:
                    node.children = expand(path + [tf], depth + 1)
                out.append(node)
            out.sort(key=lambda x: abs(x.amount), reverse=True)
            return out

        try:
            return expand([], 1)
        except Exception as e:
            logger.error("Error building contribution tree: %s", e)
            return []

    def get_top_contributors(
        self,
        result,
        impact_category: o.Ref,
        n: int = 5,
        contribution_type: str = 'process',
    ) -> List[ContributionItem]:
        """
        Get top N contributors to an impact category.

        Args:
            result: Calculation result.
            impact_category: Impact category reference.
            n: Number of top contributors to return.
            contribution_type: ``'process'`` or ``'flow'``.

        Returns:
            List of up to *n* ContributionItem objects.
        """
        if contribution_type == 'process':
            all_items = self.get_process_contributions(result, impact_category, min_share=0)
        else:
            all_items = self.get_flow_contributions(result, impact_category, min_share=0)
        return all_items[:n]

    def get_contribution_summary(
        self,
        result,
        impact_categories: Optional[List[o.Ref]] = None,
    ) -> Dict[str, List[ContributionItem]]:
        """
        Get contribution summary for multiple impact categories.

        Args:
            result: Calculation result.
            impact_categories: Categories to summarise (``None`` = all).

        Returns:
            Dict mapping category name → top-10 ContributionItem list.
        """
        summary: Dict[str, List[ContributionItem]] = {}
        try:
            if not impact_categories:
                impacts = result.get_total_impacts()
                impact_categories = [
                    iv.impact_category for iv in impacts if iv.impact_category
                ]

            for cat_ref in impact_categories:
                contribs = self.get_top_contributors(result, cat_ref, n=10)
                summary[cat_ref.name or str(cat_ref.id)] = contribs

        except Exception as e:
            logger.error("Error getting contribution summary: %s", e)

        return summary
