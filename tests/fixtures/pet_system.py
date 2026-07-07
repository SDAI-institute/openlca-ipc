"""
Shared PET-vs-PC tutorial-chain builder.

Reused by BOTH `openlca-ipc case studies/case1_repeatability.ipynb` (via
`build_notebook.py`) and `test_golden_pet_live.py`, so the notebook (a
human-readable report artifact) and the regression test can't silently drift
apart on modelling details (flow names, provider-selection rules, amounts).

Reproduces the official HvA openLCA tutorial "PET vs. PC Waterbottle
Production" (ecoinvent 3.10 Cutoff, EF 3.1) — see `openlca-ipc case studies/
case1-report.md` for the full write-up and `case1-findings.md` ("Residual
~0.78x") for why absolute totals differ from the tutorial's published PDF
while the model itself is correct.

Accepts a raw `olca_ipc.Client` (not the `OLCAClient` facade used by
`golden_system.py`) to match how the notebook already connects — this keeps
the notebook's connection cell unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import olca_schema as o
from openlca_ipc import SearchUtils, DataBuilder, SystemBuilder

# (key, flow search name, provider-name "must contain" tokens, "must not
# contain" tokens) — resolves the tutorial's Table 6 RER background providers.
SPEC = [
    ("pet_gran", "polyethylene terephthalate, granulate, bottle grade",
     ["polyethylene terephthalate production", "bottle grade"], ["market"]),
    ("hdpe", "polyethylene, high density, granulate",
     ["polyethylene production, high density"], ["market"]),
    ("pp", "polypropylene, granulate",
     ["polypropylene production, granulate"], ["market"]),
    ("pc", "polycarbonate",
     ["polycarbonate production"], ["market"]),
    ("ldpe", "polyethylene, low density, granulate",
     ["polyethylene production, low density"], ["market"]),
    ("pb", "polybutadiene",
     ["polybutadiene production"], ["market"]),
    ("transport", "transport, freight, lorry 16-32 metric ton, EURO6",
     ["transport, freight, lorry 16-32 metric ton, euro6"], ["market"]),
    ("tap_water", "tap water",
     ["market group for tap water"], []),
]

TR_TKM = 0.065 * 500 / 1000.0  # 0.0325 t*km (= 0.065 kg x 500 km)


@dataclass
class PetPcSystems:
    pet_system: o.Ref
    pc_system: o.Ref
    method: object
    created: list = field(default_factory=list)  # [(model_type, id), ...]


def _pick_flow(search: SearchUtils, name: str) -> o.Ref:
    flows = search.find_flows([name], max_results=30)
    exact = [f for f in flows if (f.name or "").lower() == name.lower()]
    return (exact or flows)[0]


def _pick_provider(search: SearchUtils, flow_ref, prefer, avoid, location="RER"):
    provs = search.find_providers(flow_ref)
    rer = [p for p in provs if (getattr(p, "location", None) or "") == location]
    pool = rer or provs

    def ok(p):
        n = (p.name or "").lower()
        return all(t in n for t in prefer) and not any(a in n for a in avoid)

    matches = [p for p in pool if ok(p)] or pool
    return matches[0]


def resolve_background(search: SearchUtils) -> dict:
    """Resolve every SPEC entry's flow + RER provider. Returns
    {key: {"flow": Ref, "provider": Ref}}."""
    bg = {}
    for key, name, prefer, avoid in SPEC:
        f = _pick_flow(search, name)
        p = _pick_provider(search, f, prefer, avoid)
        bg[key] = {"flow": f, "provider": p}
    return bg


def build_pet_pc_chain(
    client, method, tag: str = "PETPC", *, cutoff: float | None = None
) -> PetPcSystems:
    """Build the full PET + PC chain (6 flows + 6 processes + 2 systems each
    tagged `tag`) and return the two system refs + everything created (for
    cleanup). `client` is a raw `olca_ipc.Client`; `method` is the resolved
    impact method (e.g. from `search.find_impact_method(["EF v3.1"])`) —
    passed in rather than resolved here so callers only look it up once.
    `cutoff` (optional) applies a linking cut-off (openLCA tutorial ch. 6.3
    uses 0.05 for a 5% cut-off) to both product systems.
    """
    search = SearchUtils(client)
    data = DataBuilder(client)
    systems = SystemBuilder(client)
    bg = resolve_background(search)
    created: list = []

    def flow(label):
        f = data.create_product_flow(f"{tag} | {label}")
        created.append((o.Flow, f.id))
        return f

    def proc(label, exchanges):
        p = data.create_process(f"{tag} | {label}", exchanges=exchanges)
        created.append((o.Process, p.id))
        return p

    def ex(flow_ref, amount, is_input, qref=False, provider=None, formula=None):
        return data.create_exchange(flow_ref, amount, is_input,
                                    is_quantitative_reference=qref,
                                    provider=provider, formula=formula)

    def chain(prefix, gran_name, gran_inputs):
        """gran_inputs: list of (bg_key, amount) for the granulate production step."""
        g = flow(f"Granulates ({gran_name})")
        gt = flow(f"Granulates ({gran_name}), transported")
        b = flow(f"{prefix} Bottle, filled")

        prod = proc(f"{prefix} Granulate Production", [
            ex(g, 0.065, False, qref=True),
            *[ex(bg[key]["flow"], amount, True, provider=bg[key]["provider"])
              for key, amount in gran_inputs],
        ])
        trans = proc(f"{prefix} Granulate Transport", [
            ex(gt, 0.065, False, qref=True),
            ex(g, 0.065, True, provider=prod),
            ex(bg["transport"]["flow"], TR_TKM, True,
               provider=bg["transport"]["provider"], formula="0.065*500/1000"),
        ])
        fill = proc(f"{prefix} Bottle Filling", [
            ex(b, 1.065, False, qref=True),
            ex(gt, 0.065, True, provider=trans),
            ex(bg["tap_water"]["flow"], 1.0, True, provider=bg["tap_water"]["provider"]),
        ])
        sys_ref = systems.create_product_system(
            o.Ref(id=fill.id, name=fill.name, ref_type=o.RefType.Process),
            preferred_type="UNIT_PROCESS", cutoff=cutoff)
        created.append((o.ProductSystem, sys_ref.id))
        return sys_ref

    pet_sys = chain("PET", "PET, HDPE, PP",
                    [("pet_gran", 0.060), ("hdpe", 0.004), ("pp", 0.001)])
    pc_sys = chain("PC", "PC, LDPE, PB",
                   [("pc", 0.060), ("ldpe", 0.004), ("pb", 0.001)])

    return PetPcSystems(pet_system=pet_sys, pc_system=pc_sys, method=method,
                        created=created)


def cleanup_pet_pc_chain(client, built: PetPcSystems) -> None:
    """Delete every entity created for a PetPcSystems, in dependency order."""
    order = {o.ProductSystem: 0, o.Process: 1, o.Flow: 2}
    ref_type = {o.ProductSystem: o.RefType.ProductSystem,
                o.Process: o.RefType.Process, o.Flow: o.RefType.Flow}
    for model_type, uid in sorted(built.created, key=lambda t: order.get(t[0], 99)):
        try:
            client.delete(o.Ref(id=uid, ref_type=ref_type[model_type]))
        except Exception:
            pass
