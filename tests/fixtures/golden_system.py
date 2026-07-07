"""
Synthetic, license-free "golden" LCA system with a hand-calculable answer.

Unlike the Case-1 PET/PC tutorial reproduction (which requires the paid
ecoinvent 3.10 database and can drift from published numbers due to background
dataset revisions — see `openlca-ipc case studies/case1-findings.md`, "Residual
~0.78x"), this system uses ONLY entities created by the test itself: one
elementary flow, one impact category/method with a hand-picked characterization
factor, two product flows, and a 2-level unit-process chain. It runs against
ANY openLCA database (even an empty one) and has an answer you can verify with
a calculator, so it is a true independent cross-check rather than a comparison
against another modelling tool's opinion.

See `openlca-ipc case studies/case2-golden-handcalc.md` for the full derivation.

    Golden Material Production  --[3 kg Golden Material]-->  Golden Product Production
        emits 2.0 kg GOLDEN_CO2 (per 1 kg Golden Material)     emits 0.5 kg GOLDEN_CO2 directly
                                                                outputs 1 kg Golden Product (ref)

    Hand calc for 1 kg Golden Product:
        direct:   0.5 kg GOLDEN_CO2 * CF 1.0            = 0.5 kg CO2e
        upstream: 3 kg Golden Material * 2.0 kg CO2/kg
                  * CF 1.0                                = 6.0 kg CO2e
        TOTAL                                             = 6.5 kg CO2e
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

import olca_schema as o
from openlca_ipc import OLCAClient

EXPECTED_IMPACT = 6.5  # kg CO2e per 1 kg "Golden Product" — see module docstring


@dataclass
class GoldenSystem:
    """Handles + expected answer for the synthetic golden system."""

    system_ref: o.Ref
    method: o.ImpactMethod
    category_ref: o.Ref
    expected_impact: float
    created: list = field(default_factory=list)  # [(model_type, id), ...] newest-last


def build_golden_system(client: OLCAClient, prefix: str = "GOLDEN") -> GoldenSystem:
    """Build the synthetic golden system and return its handles.

    ``client`` is the agent-layer :class:`OLCAClient` facade (exposes
    ``.data``/``.systems``/``.client``), matching the convention used by the
    other live test suites. All entities are prefixed so they are trivially
    identifiable; call :func:`cleanup_golden_system` with the returned object
    when done.
    """
    data = client.data
    systems = client.systems
    raw = client.client
    created: list = []

    # -- elementary flow -----------------------------------------------
    co2 = o.Flow()
    co2.id = str(uuid.uuid4())
    co2.name = f"{prefix} CO2 (test elementary flow)"
    co2.flow_type = o.FlowType.ELEMENTARY_FLOW
    co2.flow_properties = [o.FlowPropertyFactor(
        flow_property=o.Ref(id=data.mass_property.id, name=data.mass_property.name,
                            ref_type=o.RefType.FlowProperty),
        conversion_factor=1.0, is_ref_flow_property=True)]
    raw.put(co2)
    created.append((o.Flow, co2.id))

    # -- impact category + characterization factor ----------------------
    category = o.ImpactCategory()
    category.id = str(uuid.uuid4())
    category.name = f"{prefix} GWP"
    category.ref_unit = "kg CO2e"
    category.impact_factors = [o.ImpactFactor(
        flow=o.Ref(id=co2.id, name=co2.name, ref_type=o.RefType.Flow),
        flow_property=o.Ref(id=data.mass_property.id, name=data.mass_property.name,
                            ref_type=o.RefType.FlowProperty),
        unit=o.Ref(id=data.kg_unit.id, name=data.kg_unit.name, ref_type=o.RefType.Unit),
        value=1.0,
    )]
    category_ref = raw.put(category)
    created.append((o.ImpactCategory, category_ref.id))

    # -- impact method ----------------------------------------------------
    method = o.ImpactMethod()
    method.id = str(uuid.uuid4())
    method.name = f"{prefix} Test Method"
    method.impact_categories = [o.Ref(id=category_ref.id, name=category.name,
                                      ref_type=o.RefType.ImpactCategory)]
    raw.put(method)
    created.append((o.ImpactMethod, method.id))
    method_full = raw.get(o.ImpactMethod, method.id)

    # -- product flows ------------------------------------------------------
    material = data.create_product_flow(f"{prefix} Material")
    created.append((o.Flow, material.id))
    product = data.create_product_flow(f"{prefix} Product")
    created.append((o.Flow, product.id))

    # -- upstream process: 1 kg Golden Material, emits 2.0 kg GOLDEN_CO2 ----
    material_proc = data.create_process(f"{prefix} Material Production", exchanges=[
        data.create_exchange(material, 1.0, False, is_quantitative_reference=True),
        data.create_exchange(co2, 2.0, False),  # emission: output, elementary
    ])
    created.append((o.Process, material_proc.id))

    # -- reference process: 1 kg Golden Product, consumes 3 kg Golden
    #    Material (linked to the upstream process), emits 0.5 kg directly ----
    product_proc = data.create_process(f"{prefix} Product Production", exchanges=[
        data.create_exchange(product, 1.0, False, is_quantitative_reference=True),
        data.create_exchange(material, 3.0, True, provider=material_proc),
        data.create_exchange(co2, 0.5, False),
    ])
    created.append((o.Process, product_proc.id))

    # -- product system -------------------------------------------------
    system_ref = systems.create_product_system(
        o.Ref(id=product_proc.id, name=product_proc.name, ref_type=o.RefType.Process),
        preferred_type="UNIT_PROCESS",
    )
    created.append((o.ProductSystem, system_ref.id))

    return GoldenSystem(
        system_ref=system_ref,
        method=method_full,
        category_ref=category_ref,
        expected_impact=EXPECTED_IMPACT,
        created=created,
    )


def cleanup_golden_system(client: OLCAClient, golden: GoldenSystem) -> None:
    """Delete every entity created for a GoldenSystem, in dependency order."""
    order = {
        o.ProductSystem: 0, o.Process: 1, o.ImpactMethod: 2,
        o.ImpactCategory: 3, o.Flow: 4,
    }
    ref_type = {
        o.ProductSystem: o.RefType.ProductSystem, o.Process: o.RefType.Process,
        o.ImpactMethod: o.RefType.ImpactMethod, o.ImpactCategory: o.RefType.ImpactCategory,
        o.Flow: o.RefType.Flow,
    }
    raw = client.client
    for model_type, uid in sorted(golden.created, key=lambda t: order.get(t[0], 99)):
        try:
            raw.delete(o.Ref(id=uid, ref_type=ref_type[model_type]))
        except Exception:
            pass  # best-effort cleanup
