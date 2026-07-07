# ============================================================================
# FILE: olca_utils/systems.py
# ============================================================================

"""
Product system creation and management.
"""

from typing import Optional, Union
import logging
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)

_PROVIDER_LINKING = {
    'prefer': o.ProviderLinking.PREFER_DEFAULTS,
    'only': o.ProviderLinking.ONLY_DEFAULTS,
    'ignore': o.ProviderLinking.IGNORE_DEFAULTS,
}


class SystemBuilder:
    """
    Utilities for creating and managing product systems.
    """

    def __init__(self, client: ipc.Client):
        self.client = client

    def create_product_system(
        self,
        process: Union[o.Process, o.Ref],
        name: Optional[str] = None,
        default_providers: str = 'prefer',
        preferred_type: str = 'LCI_RESULT',
        cutoff: Optional[float] = None,
    ) -> Optional[o.Ref]:
        """
        Create a product system from a process.

        Args:
            process: Process object or reference used as the root process.
            name: Optional custom name; if given, the system is renamed after
                creation (requires an extra round-trip to the server).
            default_providers: How to handle default providers when auto-linking.
                ``'prefer'`` (default) — use default providers where set,
                otherwise link freely.
                ``'only'``  — only use default providers; leave others unlinked.
                ``'ignore'`` — ignore all default providers.
            preferred_type: ``'LCI_RESULT'`` (default) links to LCI-result
                processes; ``'UNIT_PROCESS'`` prefers unit processes.
            cutoff: Optional linking cut-off in [0, 1). Providers contributing
                less than this fraction of the upstream demand are not linked
                (openLCA tutorial ch. 6.3 uses 0.05 for a 5% cut-off). ``None``
                (default) builds the full upstream network.

        Returns:
            Product system reference (o.Ref), or None on failure.
        """
        try:
            provider_linking = _PROVIDER_LINKING.get(
                default_providers, o.ProviderLinking.PREFER_DEFAULTS
            )
            config = o.LinkingConfig(
                prefer_unit_processes=(preferred_type == 'UNIT_PROCESS'),
                provider_linking=provider_linking,
            )
            if cutoff is not None:
                config.cutoff = cutoff
            system_ref = self.client.create_product_system(process, config)

            if system_ref and name:
                system = self.client.get(o.ProductSystem, system_ref.id)
                if system:
                    system.name = name
                    self.client.put(system)

            logger.info(
                "Created product system: %s",
                system_ref.name if system_ref else 'Unknown',
            )
            return system_ref

        except Exception as e:
            logger.error("Failed to create product system: %s", e)
            return None
