# ============================================================================
# FILE: olca_utils/search.py
# ============================================================================

"""
Advanced search and discovery utilities.
"""

import logging
from typing import List, Optional, Iterator
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


class SearchUtils:
    """
    Utilities for searching and discovering entities in openLCA database.
    
    Provides smart search with partial keyword matching, case-insensitive
    search, and automatic provider linking.
    """
    
    def __init__(self, client: ipc.Client):
        self.client = client
    
    def find_flows(
        self,
        keywords: List[str],
        max_results: int = 10,
        flow_type: Optional[o.FlowType] = None
    ) -> List[o.Ref]:
        """
        Search for flows using partial keyword matching.
        
        Args:
            keywords: List of keywords (case-insensitive, all must match)
            max_results: Maximum number of results
            flow_type: Optional flow type filter
        
        Returns:
            List of flow references matching all keywords
        
        Example:
            >>> flows = search.find_flows(['polyethylene', 'terephthalate'])
            >>> print(flows[0].name)
            'polyethylene terephthalate, granulate, bottle grade'
        """
        matches = []
        keywords_lower = [k.lower() for k in keywords]
        
        for flow_ref in self.client.get_descriptors(o.Flow):
            name_lower = flow_ref.name.lower()
            
            # Check if ALL keywords are present
            if all(kw in name_lower for kw in keywords_lower):
                if flow_type:
                    # Verify flow type
                    full_flow = self.client.get(o.Flow, flow_ref.id)
                    if full_flow and full_flow.flow_type == flow_type:
                        matches.append(flow_ref)
                else:
                    matches.append(flow_ref)
                
                if len(matches) >= max_results:
                    break
        
        return matches
    
    def find_flow(
        self,
        keywords: List[str],
        flow_type: Optional[o.FlowType] = None
    ) -> Optional[o.Ref]:
        """
        Find the first flow matching keywords.
        
        Args:
            keywords: Search keywords
            flow_type: Optional flow type filter
        
        Returns:
            First matching flow reference, or None
        """
        results = self.find_flows(keywords, max_results=1, flow_type=flow_type)
        return results[0] if results else None
    
    def find_providers(self, flow: o.Ref) -> List[o.Ref]:
        """
        Get all provider processes for a flow.
        
        Args:
            flow: Flow reference
        
        Returns:
            List of provider process references
        
        Example:
            >>> flow = search.find_flow(['steel'])
            >>> providers = search.find_providers(flow)
            >>> print(providers[0].name)
            'steel production'
        """
        try:
            tech_flows = list(self.client.get_providers(flow))
            
            # Extract process references from TechFlow objects
            providers = []
            for tf in tech_flows:
                if hasattr(tf, 'provider'):
                    providers.append(tf.provider)
                elif hasattr(tf, 'process'):
                    providers.append(tf.process)
                else:
                    providers.append(tf)
            
            return providers
        except Exception as e:
            logger.warning(f"Error getting providers for {flow.name}: {e}")
            return []
    
    def find_best_provider(self, flow: o.Ref) -> Optional[o.Ref]:
        """
        Get the first (best) provider for a flow.
        
        Args:
            flow: Flow reference
        
        Returns:
            First provider reference, or None
        """
        providers = self.find_providers(flow)
        return providers[0] if providers else None
    
    def find_processes(self, keywords: List[str], max_results: int = 10) -> List[o.Ref]:
        """Search for processes by keywords."""
        matches = []
        keywords_lower = [k.lower() for k in keywords]
        
        for proc_ref in self.client.get_descriptors(o.Process):
            if all(kw in proc_ref.name.lower() for kw in keywords_lower):
                matches.append(proc_ref)
                if len(matches) >= max_results:
                    break
        
        return matches
    
    def find_impact_method(self, keywords: List[str]) -> Optional[o.ImpactMethod]:
        """
        Find an impact method by keywords.

        Args:
            keywords: Method name keywords (e.g., ['TRACI'], ['ReCiPe'])

        Returns:
            Impact method object, or None
        """
        keywords_lower = [k.lower() for k in keywords]

        for method_ref in self.client.get_descriptors(o.ImpactMethod):
            if all(kw in method_ref.name.lower() for kw in keywords_lower):
                return self.client.get(o.ImpactMethod, method_ref.id)

        return None

    def get_by_name(self, model_type, name: str) -> Optional[o.Ref]:
        """
        Look up a single entity by its exact name.

        Wraps ``client.find(model_type, name)`` — an exact-match lookup that
        complements the partial keyword search of ``find_flows`` /
        ``find_processes``. Useful when the agent already knows the precise
        name (e.g. from a prior search result).

        Args:
            model_type: An olca_schema model class (``o.Flow``, ``o.Process``,
                ``o.ImpactMethod``, ``o.ProductSystem``, ...).
            name: Exact entity name.

        Returns:
            A reference (``o.Ref``) to the matching entity, or None.
        """
        try:
            return self.client.find(model_type, name)
        except Exception as e:
            type_name = getattr(model_type, '__name__', model_type)
            logger.warning("Error finding %s named %r: %s", type_name, name, e)
            return None

