# ============================================================================
# FILE: olca_utils/data.py
# ============================================================================

"""
Data creation and building utilities.
"""

import logging
from typing import List, Tuple, Optional, Union
import uuid
import olca_schema as o
import olca_ipc as ipc

logger = logging.getLogger(__name__)


class DataBuilder:
    """
    Utilities for creating and managing openLCA data entities.
    
    Provides high-level methods for creating flows, processes, and exchanges
    with automatic linking and validation.
    """
    
    def __init__(self, client: ipc.Client):
        self.client = client
        self._mass_prop = None
        self._kg_unit = None
        self._mass_unit_cfs = None

    @property
    def mass_property(self) -> o.FlowProperty:
        """Get or cache the Mass flow property."""
        if not self._mass_prop:
            self._mass_prop = self.client.get(o.FlowProperty, name="Mass")
            if not self._mass_prop:
                raise ValueError("Mass flow property not found in database")
        return self._mass_prop
    
    @property
    def kg_unit(self) -> o.Unit:
        """Get or cache the kg unit."""
        if not self._kg_unit:
            mass_prop = self.mass_property
            unit_group = self.client.get(o.UnitGroup, mass_prop.unit_group.id)
            self._kg_unit = next(
                (u for u in unit_group.units if u.name == "kg"),
                unit_group.units[0]
            )
        return self._kg_unit

    def _mass_unit_conversion_factors(self) -> dict:
        """Get or cache {unit name -> conversion factor to kg} for the Mass
        flow property's unit group."""
        if self._mass_unit_cfs is None:
            unit_group = self.client.get(o.UnitGroup, self.mass_property.unit_group.id)
            self._mass_unit_cfs = {
                u.name: u.conversion_factor for u in (unit_group.units or [])
            }
        return self._mass_unit_cfs

    def check_mass_balance(
        self, process: o.Process, *, rel_tol: float = 1e-3
    ) -> List[str]:
        """
        Check that total input mass equals total output mass for a process.

        openLCA does not enforce conservation of mass (the tutorial explicitly
        warns: input mass should equal output mass, but this is not checked
        automatically). This inspects only exchanges whose flow property is
        **Mass** (any other property — transport, energy, items, ... — is
        skipped, since summing across incompatible units would be meaningless),
        converts each to kg using the Mass unit group's conversion factors, and
        compares the input and output totals.

        Args:
            process: A process with populated ``exchanges`` (e.g. the object
                returned by :meth:`create_process`).
            rel_tol: Relative tolerance (fraction of the larger total) before a
                warning is raised.

        Returns:
            A list of warning strings; empty if balanced (or if the process has
            no Mass-property exchanges to check).

        Example:
            >>> process = data.create_process("PET Granulate Production", exchanges=[...])
            >>> for w in data.check_mass_balance(process):
            ...     print(w)
        """
        exchanges = getattr(process, "exchanges", None) or []
        unit_cfs = self._mass_unit_conversion_factors()

        total_in = 0.0
        total_out = 0.0
        seen_any = False
        for ex in exchanges:
            fp_name = getattr(ex.flow_property, "name", None)
            if fp_name != "Mass":
                continue
            unit_name = getattr(ex.unit, "name", None)
            cf = unit_cfs.get(unit_name)
            if cf is None or ex.amount is None:
                continue
            seen_any = True
            kg = ex.amount * cf
            if ex.is_input:
                total_in += kg
            else:
                total_out += kg

        if not seen_any:
            return []

        diff = total_out - total_in
        denom = max(abs(total_in), abs(total_out), 1e-12)
        rel = abs(diff) / denom
        if rel <= rel_tol:
            return []

        name = getattr(process, "name", "<unnamed>")
        return [
            f"Mass balance violated for process {name!r}: inputs sum to "
            f"{total_in:.6g} kg, outputs sum to {total_out:.6g} kg "
            f"({rel * 100:.1f}% relative difference). Conservation of mass "
            f"requires input mass to equal output mass."
        ]

    def create_product_flow(
        self,
        name: str,
        description: str = ""
    ) -> o.Flow:
        """
        Create a new product flow.
        
        Args:
            name: Flow name
            description: Optional description
        
        Returns:
            Created flow object
        
        Example:
            >>> flow = data.create_product_flow("Steel plate", "1mm thick")
            >>> print(flow.id)
        """
        flow = o.Flow()
        flow.id = str(uuid.uuid4())
        flow.name = name
        flow.description = description
        flow.flow_type = o.FlowType.PRODUCT_FLOW
        
        # Add mass property
        flow.flow_properties = [
            o.FlowPropertyFactor(
                flow_property=o.Ref(
                    id=self.mass_property.id,
                    name=self.mass_property.name,
                    ref_type=o.RefType.FlowProperty
                ),
                conversion_factor=1.0,
                is_ref_flow_property=True
            )
        ]
        
        self.client.put(flow)
        logger.info(f"Created product flow: {name}")
        return flow
    
    def _reference_property_and_unit(
        self, flow: Union[o.Flow, o.Ref]
    ) -> Tuple[o.Ref, o.Ref]:
        """Resolve the reference flow property and its reference unit for a flow.

        openLCA measures each exchange in one of the flow's own flow properties;
        the amount is interpreted in that property's unit. Using the *wrong*
        property/unit (e.g. Mass/kg for a transport flow measured in t*km) makes
        openLCA drop the unit and silently fall back to the flow's reference
        unit, producing results that are off by the unit conversion factor. So
        we always derive the correct reference property/unit from the flow.

        Falls back to Mass/kg only if the flow has no usable properties.
        """
        # Ensure we have the flow with its property factors.
        flow_obj = flow
        if isinstance(flow, o.Ref) or not getattr(flow, "flow_properties", None):
            fetched = self.client.get(o.Flow, getattr(flow, "id", None))
            flow_obj = fetched or flow

        factors = getattr(flow_obj, "flow_properties", None) or []
        ref_factor = next(
            (f for f in factors if getattr(f, "is_ref_flow_property", False)),
            factors[0] if factors else None,
        )
        if ref_factor is None or ref_factor.flow_property is None:
            # No property info available; fall back to Mass/kg.
            return (
                o.Ref(id=self.mass_property.id, name=self.mass_property.name,
                      ref_type=o.RefType.FlowProperty),
                o.Ref(id=self.kg_unit.id, name=self.kg_unit.name,
                      ref_type=o.RefType.Unit),
            )

        fp_ref = ref_factor.flow_property
        fp_ref = o.Ref(id=fp_ref.id, name=fp_ref.name,
                       ref_type=o.RefType.FlowProperty)

        # Resolve the reference unit of that flow property's unit group.
        unit_ref = None
        try:
            fp_full = self.client.get(o.FlowProperty, fp_ref.id)
            ug = self.client.get(o.UnitGroup, fp_full.unit_group.id)
            units = ug.units or []
            ref_unit = next(
                (u for u in units if getattr(u, "is_ref_unit", False)),
                next((u for u in units if u.conversion_factor == 1.0),
                     units[0] if units else None),
            )
            if ref_unit is not None:
                unit_ref = o.Ref(id=ref_unit.id, name=ref_unit.name,
                                 ref_type=o.RefType.Unit)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not resolve reference unit for %s: %s",
                           fp_ref.name, exc)

        if unit_ref is None:
            unit_ref = o.Ref(id=self.kg_unit.id, name=self.kg_unit.name,
                             ref_type=o.RefType.Unit)
        return fp_ref, unit_ref

    def create_exchange(
        self,
        flow: Union[o.Flow, o.Ref],
        amount: float,
        is_input: bool,
        is_quantitative_reference: bool = False,
        provider: Optional[o.Ref] = None,
        *,
        unit: Optional[o.Ref] = None,
        flow_property: Optional[o.Ref] = None,
        formula: Optional[str] = None,
    ) -> o.Exchange:
        """
        Create an exchange for a process.

        By default the exchange's flow property and unit are derived from the
        flow's own **reference flow property** (so the ``amount`` is interpreted
        in the correct unit — e.g. t*km for a transport flow, kg for a mass
        flow). Override ``unit`` / ``flow_property`` to record the amount in a
        non-reference property the flow actually defines.

        Args:
            flow: Flow or flow reference.
            amount: Amount, expressed in ``unit`` (default: the flow's reference
                unit).
            is_input: True for input, False for output.
            is_quantitative_reference: True if this is the process reference.
            provider: Optional provider process reference.
            unit: Optional explicit unit Ref (must belong to a flow property the
                flow defines).
            flow_property: Optional explicit flow-property Ref.
            formula: Optional openLCA amount formula (e.g. ``"0.065*500"``);
                stored on the exchange so the value is parameterised/traceable.

        Returns:
            Exchange object

        Example:
            >>> steel_flow = search.find_flow(['steel'])
            >>> steel_provider = search.find_best_provider(steel_flow)
            >>> exchange = data.create_exchange(
            ...     steel_flow,
            ...     amount=1.0,
            ...     is_input=True,
            ...     provider=steel_provider,
            ... )
        """
        ex = o.Exchange()

        # Handle flow reference
        if isinstance(flow, o.Ref):
            ex.flow = flow
        elif isinstance(flow, o.Flow):
            ex.flow = o.Ref(
                id=flow.id,
                name=flow.name,
                ref_type=o.RefType.Flow
            )
        else:
            raise TypeError(f"Flow must be Flow or Ref, not {type(flow)}")

        # Derive the correct flow property + unit from the flow unless the
        # caller supplied explicit overrides.
        if flow_property is None or unit is None:
            derived_fp, derived_unit = self._reference_property_and_unit(flow)
            flow_property = flow_property or derived_fp
            unit = unit or derived_unit

        ex.amount = amount
        if formula:
            ex.formula = formula
        ex.unit = unit
        ex.flow_property = flow_property
        ex.is_input = is_input
        ex.is_quantitative_reference = is_quantitative_reference

        # Link provider
        if provider:
            if isinstance(provider, o.Ref):
                ex.default_provider = provider
            elif hasattr(provider, 'id'):
                ex.default_provider = o.Ref(
                    id=provider.id,
                    name=provider.name,
                    ref_type=o.RefType.Process
                )

        return ex
    
    def create_process(
        self,
        name: str,
        description: str = "",
        exchanges: Optional[List[o.Exchange]] = None
    ) -> o.Process:
        """
        Create a unit process.
        
        Args:
            name: Process name
            description: Optional description
            exchanges: List of exchanges (must include exactly one qref)
        
        Returns:
            Created process object
        
        Example:
            >>> process = data.create_process(
            ...     name="Steel production",
            ...     description="Basic oxygen furnace",
            ...     exchanges=[input_ex, output_ex]
            ... )
        """
        process = o.Process()
        process.id = str(uuid.uuid4())
        process.name = name
        process.description = description
        process.process_type = o.ProcessType.UNIT_PROCESS
        
        if exchanges:
            # Set internal IDs
            for i, ex in enumerate(exchanges, start=1):
                ex.internal_id = i
            
            process.exchanges = exchanges
            process.last_internal_id = len(exchanges)
            
            # Validate quantitative reference
            qref_count = sum(1 for ex in exchanges if ex.is_quantitative_reference)
            if qref_count != 1:
                logger.warning(
                    f"Process {name} has {qref_count} qrefs (should be 1)"
                )
        
        self.client.put(process)
        logger.info(f"Created process: {name}")
        return process
