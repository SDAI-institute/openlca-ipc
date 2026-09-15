# ============================================================================
# FILE: olca_utils/search.py
# ============================================================================

"""
Advanced search and discovery utilities.
"""

import logging
import re
from typing import List, Optional, Iterator, Tuple
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """Lowercase and canonicalise a method string for matching.

    Collapses version-noise so that a query like ``"EF v3.1"`` matches a stored
    name like ``"EF 3.1 Method (adapted)"``: drops the ``v`` in ``v3.1``,
    normalises punctuation/whitespace to single spaces.
    """
    t = (text or "").lower()
    t = re.sub(r"\bv(\d)", r"\1", t)          # v3.1 -> 3.1
    t = re.sub(r"[^a-z0-9.]+", " ", t)        # punctuation -> space
    t = re.sub(r"\s+", " ", t).strip()
    return t


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

    def find_product_systems(
        self,
        keywords: Optional[List[str]] = None,
        max_results: int = 25,
    ) -> List[o.Ref]:
        """Search existing product systems by case-insensitive keywords.

        Product systems are calculation-ready database entities and therefore
        need a read-only discovery path separate from ``create_product_system``.
        All supplied keywords must occur in the descriptor name. Passing no
        keywords returns the first ``max_results`` descriptors, which is useful
        for browsing a database when the caller does not yet know a system name.

        Args:
            keywords: Optional name fragments; all fragments must match.
            max_results: Maximum number of descriptors to return.

        Returns:
            Existing product-system references only; this method never creates
            or mutates database entities.
        """
        if max_results <= 0:
            return []
        keywords_lower = [k.strip().lower() for k in (keywords or []) if k.strip()]
        matches: List[o.Ref] = []
        for system_ref in self.client.get_descriptors(o.ProductSystem):
            name_lower = (system_ref.name or "").lower()
            if all(keyword in name_lower for keyword in keywords_lower):
                matches.append(system_ref)
                if len(matches) >= max_results:
                    break
        return matches
    
    def find_impact_methods(
        self, keywords: List[str], max_results: int = 10
    ) -> List[o.Ref]:
        """
        Find impact-method descriptors matching keywords, best match first.

        Matching is version-noise tolerant (``"EF v3.1"`` matches
        ``"EF 3.1 Method (adapted)"``). Candidates are ranked by how many query
        tokens they contain, then by name length (shorter = closer).

        Args:
            keywords: Method name keywords, e.g. ``['EF v3.1']``, ``['TRACI']``.
            max_results: Maximum number of ranked candidates to return.

        Returns:
            A list of method references (possibly empty), best match first.
        """
        tokens = [tok for kw in keywords for tok in _normalize(kw).split()]
        descriptors = list(self.client.get_descriptors(o.ImpactMethod))
        if not tokens:
            return descriptors[:max_results]

        scored: List[Tuple[int, int, o.Ref]] = []
        for ref in descriptors:
            norm = _normalize(ref.name)
            hits = sum(1 for t in tokens if t in norm)
            if hits:
                scored.append((hits, -len(norm), ref))
        scored.sort(key=lambda s: (-s[0], -s[1]))
        return [ref for _, _, ref in scored[:max_results]]

    def find_impact_method(self, keywords: List[str]) -> Optional[o.ImpactMethod]:
        """
        Find the single best impact method by keywords.

        Version-noise tolerant: ``['EF v3.1']`` resolves to
        ``"EF 3.1 Method (adapted)"``. Returns the full method (with impact
        categories) or None. Prefers a candidate that contains *all* query
        tokens; otherwise falls back to the best partial match.

        Args:
            keywords: Method name keywords (e.g., ['TRACI'], ['EF v3.1']).

        Returns:
            Impact method object, or None
        """
        tokens = [tok for kw in keywords for tok in _normalize(kw).split()]
        if not tokens:
            return None
        candidates = self.find_impact_methods(keywords, max_results=25)
        if not candidates:
            return None

        # Single-method resolution is intentionally strict: every normalized
        # query token must occur in the chosen method name.  Ranked partial
        # matches remain available through ``find_impact_methods`` for browsing,
        # but silently substituting a partial match in a calculation can produce
        # scientifically valid-looking results for the wrong LCIA method.
        full = [
            ref for ref in candidates
            if all(t in _normalize(ref.name) for t in tokens)
        ]
        if not full:
            return None
        return self.client.get(o.ImpactMethod, full[0].id)

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

