

# ============================================================================
# FILE: olca_utils/calculations.py
# ============================================================================

"""
Calculation execution and management.
"""

import logging
from typing import Dict, Optional, Union
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


class CalculationManager:
    """
    Utilities for setting up and executing calculations.
    """
    
    def __init__(self, client: ipc.Client):
        self.client = client
    
    def simple_calculation(
        self,
        system: o.Ref,
        impact_method: Optional[o.ImpactMethod] = None,
        amount: float = 1.0,
        *,
        allocation: Optional[Union[str, o.AllocationType]] = None,
    ):
        """
        Perform a simple calculation.

        Args:
            system: Product system reference
            impact_method: Optional impact method
            amount: Reference amount (default: 1.0)
            allocation: Optional allocation method for multi-output processes
                (``o.AllocationType`` or its string value, e.g.
                ``"PHYSICAL_ALLOCATION"``, ``"ECONOMIC_ALLOCATION"``,
                ``"CAUSAL_ALLOCATION"``). Applies each process's own
                pre-declared ``allocation_factors`` for that method; has no
                effect on processes with a single reference product.

        Returns:
            Calculation result

        Example:
            >>> result = calculate.simple_calculation(
            ...     system=my_system,
            ...     impact_method=traci_method,
            ...     amount=1.0
            ... )
            >>> # Don't forget to dispose!
            >>> result.dispose()
        """
        setup = o.CalculationSetup()
        setup.target = system
        setup.amount = amount

        if impact_method:
            setup.impact_method = (
                impact_method.to_ref()
                if hasattr(impact_method, 'to_ref')
                else impact_method
            )

        if allocation is not None:
            setup.allocation = (
                allocation if isinstance(allocation, o.AllocationType)
                else o.AllocationType(allocation)
            )

        result = self.client.calculate(setup)
        result.wait_until_ready()

        logger.info("Calculation complete for %s", system.name)
        return result

    def contribution_analysis(
        self,
        system: o.Ref,
        impact_method: Union[o.ImpactMethod, o.Ref],
        amount: float = 1.0
    ):
        """Perform contribution analysis."""
        setup = o.CalculationSetup()
        setup.target = system
        setup.impact_method = (
            impact_method.to_ref()
            if hasattr(impact_method, 'to_ref')
            else impact_method
        )
        setup.amount = amount

        result = self.client.calculate(setup)
        result.wait_until_ready()
        return result

    def compare_systems(
        self,
        system1: o.Ref,
        system2: o.Ref,
        impact_method: Union[o.ImpactMethod, o.Ref],
        amount: float = 1.0,
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare two product systems on the same impact method.

        Runs a calculation for each system, disposing both results, and
        aligns their total impacts by category name. The returned dict matches
        the shape consumed by ``ExportManager.export_comparison_to_csv``.

        Args:
            system1: First product system reference.
            system2: Second product system reference.
            impact_method: Impact method (``o.ImpactMethod`` or ``o.Ref``).
            amount: Reference amount for both calculations (default 1.0).

        Returns:
            Dict mapping impact-category name to
            ``{'system1', 'system2', 'difference', 'percent_diff'}``, where
            ``difference`` is system2 - system1 and ``percent_diff`` is relative
            to system1 (NaN if system1 is 0).
        """
        def totals(system: o.Ref) -> Dict[str, float]:
            result = self.simple_calculation(
                system=system, impact_method=impact_method, amount=amount
            )
            try:
                out: Dict[str, float] = {}
                for iv in result.get_total_impacts():
                    cat = iv.impact_category
                    if cat:
                        out[cat.name] = iv.amount if iv.amount is not None else 0.0
                return out
            finally:
                result.dispose()

        t1 = totals(system1)
        t2 = totals(system2)

        comparison: Dict[str, Dict[str, float]] = {}
        for name in sorted(set(t1) | set(t2)):
            v1 = t1.get(name, 0.0)
            v2 = t2.get(name, 0.0)
            diff = v2 - v1
            pct = (diff / v1 * 100.0) if v1 else float('nan')
            comparison[name] = {
                'system1': v1,
                'system2': v2,
                'difference': diff,
                'percent_diff': pct,
            }
        return comparison

