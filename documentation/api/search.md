# SearchUtils API Reference

## Class: `SearchUtils`

Utilities for searching and discovering entities in the openLCA database. Provides smart search with partial keyword matching, case-insensitive search, and automatic provider linking.

**Access:** `client.search`

### Methods

---

## `find_flows()`

Search for flows using partial keyword matching.

```python
find_flows(
    keywords: List[str],
    max_results: int = 10,
    flow_type: Optional[o.FlowType] = None
) -> List[o.Ref]
```

**Parameters:**
- `keywords` (List[str]): List of keywords to match. All keywords must be present in the flow name (case-insensitive).
- `max_results` (int, optional): Maximum number of results to return. Default: 10.
- `flow_type` (Optional[o.FlowType], optional): Filter by flow type (ELEMENTARY_FLOW, PRODUCT_FLOW, WASTE_FLOW). Default: None (all types).

**Returns:**
- `List[o.Ref]`: List of flow references matching all keywords.

**Example:**
```python
with OLCAClient(port=8080) as client:
    # Find flows containing both 'polyethylene' and 'terephthalate'
    pet_flows = client.search.find_flows(['polyethylene', 'terephthalate'])

    for flow in pet_flows:
        print(flow.name)
    # Output: 'polyethylene terephthalate, granulate, bottle grade'

    # Find only product flows
    products = client.search.find_flows(
        ['steel'],
        flow_type=o.FlowType.PRODUCT_FLOW
    )

    # Limit results
    top_5 = client.search.find_flows(['electricity'], max_results=5)
```

**Tips:**
- Keywords are case-insensitive
- All keywords must be present (AND logic, not OR)
- Use broader keywords for more results
- Use specific keywords to narrow down results

---

## `find_flow()`

Find the first flow matching keywords.

```python
find_flow(
    keywords: List[str],
    flow_type: Optional[o.FlowType] = None
) -> Optional[o.Ref]
```

**Parameters:**
- `keywords` (List[str]): Search keywords.
- `flow_type` (Optional[o.FlowType], optional): Filter by flow type. Default: None.

**Returns:**
- `Optional[o.Ref]`: First matching flow reference, or None if not found.

**Example:**
```python
with OLCAClient(port=8080) as client:
    # Find first match
    steel = client.search.find_flow(['steel'])

    if steel:
        print(f"Found: {steel.name}")
    else:
        print("Material not found in database")

    # Find specific product
    pet = client.search.find_flow(
        ['polyethylene', 'terephthalate'],
        flow_type=o.FlowType.PRODUCT_FLOW
    )
```

**When to Use:**
- When you need a single result
- When you're confident the first match is correct
- When you want to quickly check if a material exists

**Note:** This is equivalent to `find_flows(keywords, max_results=1)[0]` but handles empty results gracefully.

---

## `find_providers()`

Get all provider processes for a flow.

```python
find_providers(flow: o.Ref) -> List[o.Ref]
```

**Parameters:**
- `flow` (o.Ref): Flow reference to find providers for.

**Returns:**
- `List[o.Ref]`: List of provider process references. Empty list if no providers found.

**Example:**
```python
with OLCAClient(port=8080) as client:
    # Find a flow
    steel = client.search.find_flow(['steel'])

    # Get all providers
    providers = client.search.find_providers(steel)

    print(f"Found {len(providers)} providers for {steel.name}:")
    for provider in providers:
        print(f"  - {provider.name}")
```

**Use Cases:**
- Finding all processes that produce a material
- Comparing different production routes
- Validating material availability in database

---

## `find_best_provider()`

Get the first (best) provider for a flow.

```python
find_best_provider(flow: o.Ref) -> Optional[o.Ref]
```

**Parameters:**
- `flow` (o.Ref): Flow reference to find provider for.

**Returns:**
- `Optional[o.Ref]`: First provider reference, or None if no providers found.

**Example:**
```python
with OLCAClient(port=8080) as client:
    # Find flow and its provider
    steel = client.search.find_flow(['steel'])
    provider = client.search.find_best_provider(steel)

    if provider:
        print(f"Provider: {provider.name}")

        # Use provider in exchange
        exchange = client.data.create_exchange(
            steel,
            amount=1.0,
            is_input=True,
            provider=provider
        )
    else:
        print("No provider found - material may be elementary flow")
```

**When to Use:**
- When you need a single provider
- When any provider is acceptable
- In automated workflows

**Note:** Returns the first provider found. Use `find_providers()` if you need to choose from multiple options.

---

## `find_processes()`

Search for processes by keywords.

```python
find_processes(
    keywords: List[str],
    max_results: int = 10
) -> List[o.Ref]
```

**Parameters:**
- `keywords` (List[str]): Process name keywords (case-insensitive, all must match).
- `max_results` (int, optional): Maximum results. Default: 10.

**Returns:**
- `List[o.Ref]`: List of process references matching all keywords.

**Example:**
```python
with OLCAClient(port=8080) as client:
    # Find production processes
    steel_production = client.search.find_processes(['steel', 'production'])

    for proc in steel_production:
        print(proc.name)

    # Find transport processes
    transport = client.search.find_processes(['transport', 'truck'])
```

**Use Cases:**
- Finding existing processes
- Identifying processes for analysis
- Discovering available production routes

---

## `find_impact_method()`

Find an impact method by keywords.

```python
find_impact_method(keywords: List[str]) -> Optional[o.ImpactMethod]
```

**Parameters:**
- `keywords` (List[str]): Method name keywords (e.g., ['TRACI'], ['ReCiPe']).

**Returns:**
- `Optional[o.ImpactMethod]`: Impact method object, or None if not found.

**Example:**
```python
with OLCAClient(port=8080) as client:
    # Find TRACI method
    traci = client.search.find_impact_method(['TRACI'])

    if traci:
        print(f"Method: {traci.name}")
        print(f"Categories: {len(traci.impact_categories)}")
    else:
        print("Method not found in database")

    # Find ReCiPe method
    recipe = client.search.find_impact_method(['ReCiPe'])

    # Use in calculation
    if traci:
        result = client.calculate.simple_calculation(system, traci)
```

**Common Methods:**
- `['TRACI']` - Tool for Reduction and Assessment of Chemicals and Other Environmental Impacts
- `['ReCiPe']` - ReCiPe impact assessment method
- `['CML']` - CML impact assessment method
- `['ILCD']` - ILCD recommended methods

**Note:** Returns the full `ImpactMethod` object (not just a reference), ready for use in calculations.

---

## Usage Patterns

### Basic Search Workflow

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # 1. Search for material
    steel = client.search.find_flow(['steel'])

    if not steel:
        print("Steel not found!")
        exit(1)

    # 2. Find provider
    provider = client.search.find_best_provider(steel)

    if not provider:
        print("No provider found!")
        exit(1)

    # 3. Use in process
    exchange = client.data.create_exchange(
        steel,
        amount=1.0,
        is_input=True,
        provider=provider
    )
```

### Handling Missing Results

```python
with OLCAClient(port=8080) as client:
    # Try multiple keyword combinations
    pet = client.search.find_flow(['polyethylene', 'terephthalate'])

    if not pet:
        # Try abbreviated name
        pet = client.search.find_flow(['PET'])

    if not pet:
        # Try broader search
        pet_flows = client.search.find_flows(['polyethylene'], max_results=20)
        # Let user choose from list
        for i, flow in enumerate(pet_flows):
            print(f"{i+1}. {flow.name}")
```

### Exploring Results

```python
with OLCAClient(port=8080) as client:
    # Find all steel-related flows
    steel_flows = client.search.find_flows(['steel'], max_results=50)

    print(f"Found {len(steel_flows)} steel-related flows:")

    # Group by type
    products = []
    elementary = []

    for flow_ref in steel_flows:
        # Get full flow to check type
        flow = client.client.get(o.Flow, flow_ref.id)
        if flow.flow_type == o.FlowType.PRODUCT_FLOW:
            products.append(flow_ref)
        elif flow.flow_type == o.FlowType.ELEMENTARY_FLOW:
            elementary.append(flow_ref)

    print(f"  Products: {len(products)}")
    print(f"  Elementary flows: {len(elementary)}")
```

### Validating Database Content

```python
with OLCAClient(port=8080) as client:
    # Check if required materials exist
    required_materials = [
        ['steel'],
        ['aluminum'],
        ['electricity'],
        ['water']
    ]

    missing = []
    for keywords in required_materials:
        flow = client.search.find_flow(keywords)
        if not flow:
            missing.append(keywords)

    if missing:
        print("Missing materials in database:")
        for keywords in missing:
            print(f"  - {' '.join(keywords)}")
    else:
        print("All required materials found!")
```

## Search Tips

### Keyword Strategy

1. **Start Broad, Then Narrow**
   ```python
   # Too specific - may miss results
   steel = client.search.find_flow(['steel', 'hot', 'rolled', 'coil'])

   # Better - broader search
   steels = client.search.find_flows(['steel', 'hot'], max_results=20)
   ```

2. **Use Common Terms**
   ```python
   # Better
   pet = client.search.find_flow(['polyethylene', 'terephthalate'])

   # Alternative
   pet = client.search.find_flow(['PET'])
   ```

3. **Check Variants**
   ```python
   # Try both spellings
   aluminum = client.search.find_flow(['aluminum'])
   if not aluminum:
       aluminum = client.search.find_flow(['aluminium'])
   ```

### Performance Optimization

```python
# Limit results for faster searches
top_matches = client.search.find_flows(['electricity'], max_results=5)

# Use specific types to reduce search space
products_only = client.search.find_flows(
    ['steel'],
    flow_type=o.FlowType.PRODUCT_FLOW,
    max_results=10
)
```

## Troubleshooting

### No Results Found

**Problem:** `find_flow()` returns None

**Solutions:**
1. Try broader keywords
2. Check spelling and variants
3. List all flows to verify database content:
   ```python
   all_flows = client.client.get_descriptors(o.Flow)
   for flow in all_flows[:50]:  # First 50
       print(flow.name)
   ```

### Wrong Material Found

**Problem:** First match is not the desired material

**Solutions:**
1. Use more specific keywords
2. Use `find_flows()` to see all matches
3. Filter by flow type
4. Manually select from results

### No Provider Found

**Problem:** `find_best_provider()` returns None

**Possible Causes:**
- Flow is an elementary flow (no providers)
- Database doesn't have production processes
- Flow is a waste flow

**Solution:**
```python
flow = client.search.find_flow(['CO2'])
provider = client.search.find_best_provider(flow)
if not provider:
    # Check if elementary flow
    full_flow = client.client.get(o.Flow, flow.id)
    if full_flow.flow_type == o.FlowType.ELEMENTARY_FLOW:
        print(f"{flow.name} is an elementary flow - no provider needed")
```

## See Also

- [DataBuilder](data.md) - Using search results to create data
- [OLCAClient](client.md) - Client setup and connection
- [Quick Start Guide](../quickstart.md) - Getting started
