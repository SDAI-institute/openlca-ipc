"""
    Complete Life Cycle Assessment: PET vs PC Bottles
    
    
    A script to demonstrate a full LCA workflow using openLCA IPC:
    
    """
    
#%%    
import olca_schema as o
import olca_ipc as ipc
    
#%%     
# Connect to ipc
client = ipc.Client(8080)    
print("\n✓ Connected to openLCA IPC server")

#%%

# ============================================================================
# PHASE 1: GOAL AND SCOPE
# ============================================================================
print("""
Goal: Compare environmental impacts of PET vs PC bottles
Functional Unit: 1 filled bottle (0.065 kg + 1 kg water)
System Boundary: Cradle-to-gate
Database: ecoinvent 3.7.2 cutoff unit regionalized
""")
    
# Define functional unit
functional_unit = 1.065  # kg (0.065 kg bottle + 1 kg water)

# Define system boundary
# system_boundary =

# Define database



#%%

# ============================================================================
# PHASE 2: INVENTORY ANALYSIS
# ============================================================================

print("="*70)
print("PHASE 2: LIFE CYCLE INVENTORY ANALYSIS")
print("="*70)
# Get Standard References


#%%

# ----------------------------------------------------------------------------
# Get Standard References
# ----------------------------------------------------------------------------

mass_prop = client.get(o.FlowProperty, name="Mass")
if not mass_prop:
    raise ValueError("Mass flow property not found in database")
print(f"\n✓ Retrieved Mass flow property: {mass_prop.id} - {mass_prop.name}")

#%%

mass_prop_full = client.get(o.FlowProperty, mass_prop.id)
unit_group = client.get(o.UnitGroup, mass_prop_full.unit_group.id)
kg_unit = next((u for u in unit_group.units if u.name == "kg"), unit_group.units[0])
print(f"\n✓ Retrieved kg unit: {kg_unit.id} - {kg_unit.name}")


#%%


# ----------------------------------------------------------------------------
# Search for Background Processes
# ----------------------------------------------------------------------------
def find_flow_by_keywords(keywords, max_results=5):
    """
    Search flows using partial keyword matching.
    
    Args:
        keywords: list of keywords (case-insensitive)
        max_results: maximum number of results to show
    
    Returns:
        list of matching flow references
    """
    matches = []
    keywords_lower = [k.lower() for k in keywords]
    
    print(  f"  Searching: {' + '.join(keywords)}")
    
    for flow_ref in client.get_descriptors(o.Flow):
        name_lower = flow_ref.name.lower()
        
        # Check if ALL keywords are in the flow name
        if all(kw in name_lower for kw in keywords_lower):
            matches.append(flow_ref)
            if len(matches) <= max_results:
                print(f"    → {flow_ref.name}")
    
    if len(matches) > max_results:
        print(f"    ... and {len(matches) - max_results} more matches")
    elif len(matches) == 0:
        print(f"    ✗ No matches found")
    
    return matches

def find_best_provider(flow_ref):
    """Get the first (best) provider process for a flow"""
    # Handle both method names for compatibility
    try:
        if hasattr(client, 'get_providers'):
            providers = list(client.get_providers(flow_ref))
        else:
            providers = list(client.get_providers_of(flow_ref))
    except Exception as e:
        print(f"    ⚠ Error getting providers: {e}")
        return None
    
    if providers:
        # TechFlow has 'provider' attribute which is the process Ref
        first = providers[0]
        if hasattr(first, 'provider'):
            return first.provider  # Return the process Ref
        elif hasattr(first, 'process'):
            return first.process  # Alternative attribute name
        else:
            return first  # Fallback
    return None


#%%
# Store materials
materials_flows = {}
materials_providers = {}




#%%
print("=== SEARCHING FOR MATERIALS ===\n")

# PET - Polyethylene Terephthalate
print("1. PET (Polyethylene Terephthalate)")
matches = find_flow_by_keywords(['polyethylene', 'terephthalate', 'granulate', 'bottle'])
if not matches:
    matches = find_flow_by_keywords(['polyethylene', 'terephthalate', 'granulate'])
if matches:
    materials_flows['PET'] = matches[0]
    materials_providers['PET'] = find_best_provider(matches[0])
    if materials_providers['PET']:
        prov = materials_providers['PET']
        prov_name = prov.name if hasattr(prov, 'name') else str(prov)
        print(f"  ✓ Provider: {prov_name}\n")
    else:
        print(f"  ⚠ No provider found\n")
else:
    print("  ⚠ Not found\n")


# HDPE - High Density Polyethylene
print("2. HDPE (High Density Polyethylene)")
matches = find_flow_by_keywords(['polyethylene', 'high density', 'granulate'])
if matches:
    materials_flows['HDPE'] = matches[0]
    materials_providers['HDPE'] = find_best_provider(matches[0])
    if materials_providers['HDPE']:
        prov = materials_providers['HDPE']
        prov_name = prov.name if hasattr(prov, 'name') else str(prov)
        print(f"  ✓ Provider: {prov_name}\n")
    else:
        print(f"  ⚠ No provider found\n")
else:
    print("  ⚠ Not found\n")

# PP - Polypropylene
print("3. PP (Polypropylene)")
matches = find_flow_by_keywords(['polypropylene', 'granulate'])
if matches:
    materials_flows['PP'] = matches[0]
    materials_providers['PP'] = find_best_provider(matches[0])
    if materials_providers['PP']:
        prov = materials_providers['PP']
        prov_name = prov.name if hasattr(prov, 'name') else str(prov)
        print(f"  ✓ Provider: {prov_name}\n")
    else:
        print(f"  ⚠ No provider found\n")
else:
    print("  ⚠ Not found\n")

# PC - Polycarbonate
print("4. PC (Polycarbonate)")
matches = find_flow_by_keywords(['polycarbonate', 'granulate'])
if not matches:
    matches = find_flow_by_keywords(['polycarbonate'])
if matches:
    materials_flows['PC'] = matches[0]
    materials_providers['PC'] = find_best_provider(matches[0])
    if materials_providers['PC']:
        prov = materials_providers['PC']
        prov_name = prov.name if hasattr(prov, 'name') else str(prov)
        print(f"  ✓ Provider: {prov_name}\n")
    else:
        print(f"  ⚠ No provider found\n")
else:
    print("  ⚠ Not found\n")

# LDPE - Low Density Polyethylene
print("5. LDPE (Low Density Polyethylene)")
matches = find_flow_by_keywords(['polyethylene', 'low density', 'granulate'])
if matches:
    materials_flows['LDPE'] = matches[0]
    materials_providers['LDPE'] = find_best_provider(matches[0])
    if materials_providers['LDPE']:
        prov = materials_providers['LDPE']
        prov_name = prov.name if hasattr(prov, 'name') else str(prov)
        print(f"  ✓ Provider: {prov_name}\n")
    else:
        print(f"  ⚠ No provider found\n")
else:
    print("  ⚠ Not found\n")

# PB - Polybutadiene
print("6. PB (Polybutadiene)")
matches = find_flow_by_keywords(['polybutadiene'])
if matches:
    materials_flows['PB'] = matches[0]
    materials_providers['PB'] = find_best_provider(matches[0])
    if materials_providers['PB']:
        prov = materials_providers['PB']
        prov_name = prov.name if hasattr(prov, 'name') else str(prov)
        print(f"  ✓ Provider: {prov_name}\n")
    else:
        print(f"  ⚠ No provider found\n")
else:
    print("  ⚠ Not found\n")

# Water
print("7. Water (Tap Water)")
matches = find_flow_by_keywords(['tap', 'water'])
if not matches:
    matches = find_flow_by_keywords(['water', 'decarbonised'])
if matches:
    materials_flows['Water'] = matches[0]
    materials_providers['Water'] = find_best_provider(matches[0])
    if materials_providers['Water']:
        prov = materials_providers['Water']
        prov_name = prov.name if hasattr(prov, 'name') else str(prov)
        print(f"  ✓ Provider: {prov_name}\n")
    else:
        print(f"   No provider found\n")
else:
    print("  Not found\n")
    
#%%
# Print summary
print("="*70)
print("SEARCH SUMMARY")
print("="*70)

found_count = len(materials_flows)
total_count = 7
print(f"Found {found_count}/{total_count} materials with providers\n")

for mat in ['PET', 'HDPE', 'PP', 'PC', 'LDPE', 'PB', 'Water']:
    status = "✓" if mat in materials_flows else "✗"
    print(f"  {status} {mat}")

if 'PET' not in materials_flows or 'PC' not in materials_flows:
    print("\n WARNING: Missing critical materials!")
    print("Script will continue with available materials...\n")

#%%
# ----------------------------------------------------------------------------
# Create Product Flows
# ----------------------------------------------------------------------------
def create_flow(name):
    """Create a product flow"""
    flow = o.Flow()
    flow.name = name
    flow.flow_type = o.FlowType.PRODUCT_FLOW
    
    flow.flow_properties = [
        o.FlowPropertyFactor(
            flow_property=o.Ref(
                id=mass_prop.id,
                name=mass_prop.name,
                ref_type=o.RefType.FlowProperty
            ),
            conversion_factor=1.0,
            is_ref_flow_property=True
        )
    ]
    
    client.put(flow)
    print(f"  ✓ {name}")
    return flow



# PET flows
pet_mix = create_flow("PET granulate mix")
pet_mix_trans = create_flow("PET granulate mix, transported")
pet_bottle = create_flow("PET bottle, filled")

# PC flows
pc_mix = create_flow("PC granulate mix")
pc_mix_trans = create_flow("PC granulate mix, transported")
pc_bottle = create_flow("PC bottle, filled")


#%%
# ----------------------------------------------------------------------------
# Create Processes
# ----------------------------------------------------------------------------

print("\n--- Creating Processes ---")

def make_exchange(flow_ref, amount, is_input, is_qref=False, provider_ref=None):
    """Create an exchange with proper linking"""
    ex = o.Exchange()
    
    # Handle flow reference
    if isinstance(flow_ref, o.Ref):
        ex.flow = flow_ref
    elif isinstance(flow_ref, o.Flow):
        ex.flow = o.Ref(id=flow_ref.id, name=flow_ref.name, ref_type=o.RefType.Flow)
    elif hasattr(flow_ref, 'id'):
        ex.flow = o.Ref(id=flow_ref.id, name=flow_ref.name, ref_type=o.RefType.Flow)
    
    ex.amount = amount
    ex.unit = o.Ref(id=kg_unit.id, name=kg_unit.name, ref_type=o.RefType.Unit)
    ex.flow_property = o.Ref(id=mass_prop.id, name=mass_prop.name, ref_type=o.RefType.FlowProperty)
    ex.is_input = is_input
    ex.is_quantitative_reference = is_qref
    
    # Link provider
    if provider_ref:
        if isinstance(provider_ref, o.Ref):
            ex.default_provider = provider_ref
        elif hasattr(provider_ref, 'id'):
            ex.default_provider = o.Ref(
                id=provider_ref.id,
                name=provider_ref.name,
                ref_type=o.RefType.Process
            )
    
    return ex


def create_process(name, description, exchanges):
    """Create a process"""
    process = o.Process()
    process.name = name
    process.description = description
    process.process_type = o.ProcessType.UNIT_PROCESS
    
    for i, ex in enumerate(exchanges, start=1):
        ex.internal_id = i
    
    process.exchanges = exchanges
    process.last_internal_id = len(exchanges)
    
    client.put(process)
    print(f"  ✓ {name}")
    return process


#%%


# PET Production Chain
print("\nPET Production Chain:")

# PET Granulate Production
ex_pet_prod = [make_exchange(pet_mix, 0.065, False, True)]
if 'PET' in materials_flows:
    ex_pet_prod.append(make_exchange(materials_flows['PET'], 0.060, True, 
                                     provider_ref=materials_providers.get('PET')))
if 'HDPE' in materials_flows:
    ex_pet_prod.append(make_exchange(materials_flows['HDPE'], 0.004, True,
                                     provider_ref=materials_providers.get('HDPE')))
if 'PP' in materials_flows:
    ex_pet_prod.append(make_exchange(materials_flows['PP'], 0.001, True,
                                     provider_ref=materials_providers.get('PP')))

pet_prod = create_process(
    "PET Granulate Production",
    "Mixing PET (60g) + HDPE (4g) + PP (1g)",
    ex_pet_prod
)


# PET Transport
pet_trans = create_process(
    "PET Granulate Transport",
    "Transport 500 km by lorry",
    [
        make_exchange(pet_mix_trans, 0.065, False, True),
        make_exchange(pet_mix, 0.065, True, provider_ref=pet_prod)
    ]
)

# PET Filling
ex_pet_fill = [
    make_exchange(pet_bottle, 1.065, False, True),
    make_exchange(pet_mix_trans, 0.065, True, provider_ref=pet_trans)
]
if 'Water' in materials_flows:
    ex_pet_fill.append(make_exchange(materials_flows['Water'], 1.0, True,
                                     provider_ref=materials_providers.get('Water')))

pet_fill = create_process(
    "PET Bottle Filling",
    "Filling with 1L water",
    ex_pet_fill
)

# PC Production Chain
print("\nPC Production Chain:")

# PC Granulate Production
ex_pc_prod = [make_exchange(pc_mix, 0.065, False, True)]
if 'PC' in materials_flows:
    ex_pc_prod.append(make_exchange(materials_flows['PC'], 0.060, True,
                                    provider_ref=materials_providers.get('PC')))
if 'LDPE' in materials_flows:
    ex_pc_prod.append(make_exchange(materials_flows['LDPE'], 0.004, True,
                                    provider_ref=materials_providers.get('LDPE')))
if 'PB' in materials_flows:
    ex_pc_prod.append(make_exchange(materials_flows['PB'], 0.001, True,
                                    provider_ref=materials_providers.get('PB')))

pc_prod = create_process(
    "PC Granulate Production",
    "Mixing PC (60g) + LDPE (4g) + PB (1g)",
    ex_pc_prod
)

# PC Transport
pc_trans = create_process(
    "PC Granulate Transport",
    "Transport 500 km by lorry",
    [
        make_exchange(pc_mix_trans, 0.065, False, True),
        make_exchange(pc_mix, 0.065, True, provider_ref=pc_prod)
    ]
)

# PC Filling
ex_pc_fill = [
    make_exchange(pc_bottle, 1.065, False, True),
    make_exchange(pc_mix_trans, 0.065, True, provider_ref=pc_trans)
]
if 'Water' in materials_flows:
    ex_pc_fill.append(make_exchange(materials_flows['Water'], 1.0, True,
                                    provider_ref=materials_providers.get('Water')))

pc_fill = create_process(
    "PC Bottle Filling",
    "Filling with 1L water",
    ex_pc_fill
)

#%%

# ----------------------------------------------------------------------------
# Create Product Systems
# ----------------------------------------------------------------------------
print("\n--- Creating Product Systems ---")

