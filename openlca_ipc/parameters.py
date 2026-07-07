# ============================================================================
# FILE: olca_utils/parameters.py
# ============================================================================

"""
Parameter management and scenario analysis.
"""

import logging
from typing import List, Dict, Optional
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


class ParameterManager:
    """
    Utilities for parameter redefinition and scenario analysis.
    
    Enables sensitivity analysis by varying parameter values and
    running multiple calculations.
    """
    
    def __init__(self, client: ipc.Client):
        self.client = client
    
    def create_parameter_redef(
        self,
        name: str,
        value: float,
        context: Optional[o.Ref] = None
    ) -> o.ParameterRedef:
        """
        Create a parameter redefinition.
        
        Args:
            name: Parameter name
            value: New parameter value
            context: Optional process/method context (None for global)
        
        Returns:
            ParameterRedef object
        
        Example:
            >>> redef = parameters.create_parameter_redef(
            ...     name='transport_distance',
            ...     value=1000
            ... )
        """
        redef = o.ParameterRedef()
        redef.name = name
        redef.value = value
        if context:
            redef.context = context
        return redef

    def find_global_parameter(self, name: str) -> Optional[o.Ref]:
        """Return the global parameter descriptor with this name, or None."""
        target = (name or "").strip().lower()
        try:
            for ref in self.client.get_descriptors(o.Parameter):
                if (ref.name or "").strip().lower() == target:
                    return ref
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not list global parameters: %s", exc)
        return None

    def run_scenario_analysis(
        self,
        system: o.Ref,
        impact_method: o.ImpactMethod,
        parameter_name: str,
        values: List[float],
        context: Optional[o.Ref] = None
    ) -> Dict[float, List[Dict]]:
        """
        Run scenario analysis by varying a parameter.
        
        Args:
            system: Product system
            impact_method: Impact method
            parameter_name: Parameter to vary
            values: List of parameter values to test
            context: Optional parameter context
        
        Returns:
            Dictionary mapping parameter values to impact results
        
        Example:
            >>> # Analyze effect of transport distance
            >>> results = parameters.run_scenario_analysis(
            ...     system=my_system,
            ...     impact_method=traci,
            ...     parameter_name='transport_distance',
            ...     values=[100, 500, 1000, 2000]
            ... )
            >>> 
            >>> for distance, impacts in results.items():
            ...     gwp = next(i for i in impacts if 'warming' in i['name'].lower())
            ...     print(f"{distance} km: {gwp['amount']:.4e}")
        """
        # Guard against the silent no-op trap: openLCA ignores a ParameterRedef
        # whose parameter does not exist, so every "scenario" would return the
        # baseline and look meaningful while varying nothing. Require the
        # parameter to be resolvable (an explicit ``context`` for a local
        # parameter, or a matching global parameter) before running.
        if context is None and self.find_global_parameter(parameter_name) is None:
            raise ValueError(
                f"Parameter {parameter_name!r} was not found as a global "
                f"parameter in the database. Scenario analysis would silently "
                f"vary nothing. Provide a `context` (the process Ref that owns "
                f"the local parameter), or define {parameter_name!r} as a global "
                f"parameter first."
            )

        results = {}

        for value in values:
            logger.info(f"Running scenario: {parameter_name} = {value}")
            
            # Create setup with parameter redefinition
            setup = o.CalculationSetup()
            setup.target = system
            setup.impact_method = (
                impact_method.to_ref()
                if hasattr(impact_method, 'to_ref')
                else impact_method
            )
            setup.amount = 1.0
            setup.parameters = [self.create_parameter_redef(parameter_name, value, context)]
            
            # Calculate
            result = self.client.calculate(setup)
            result.wait_until_ready()
            
            # Extract impacts
            impacts = []
            for imp in result.get_total_impacts():
                amount = (imp.amount if hasattr(imp, 'amount') else
                         imp.value if hasattr(imp, 'value') else 0)
                impacts.append({
                    'name': imp.impact_category.name,
                    'amount': amount
                })
            
            results[value] = impacts
            result.dispose()
        
        return results

