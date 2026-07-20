# Quick Start Guide

Get up and running with the openLCA IPC Python library in 5 minutes.

## Prerequisites

Before starting, make sure you have:

1. ✓ Python 3.11 or higher installed
2. ✓ openLCA desktop application installed
3. ✓ The library installed (see [Installation Guide](../documentation/installation.md))
4. ✓ A database loaded in openLCA

## Step 1: Start openLCA IPC Server

1. Open openLCA desktop application
2. Open a database (File → Open Database)
3. Go to **Tools → Developer Tools → IPC Server**
4. Click **Start**
5. Note the port (default: 8080)

Keep openLCA and the IPC server running throughout this tutorial.

## Step 2: Test Connection

Create a new Python file `test.py`:

```python
from openlca_ipc import OLCAClient

# Connect to openLCA
client = OLCAClient(port=8080)

# Test connection
if client.test_connection():
    print("✓ Connected to openLCA!")
else:
    print("✗ Connection failed")
```

Run it:
```bash
python test.py
```

**Expected output:**
```
✓ Connected to openLCA!
```

## Step 3: Your First Search

Let's search for a material in the database:

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Search for steel
    steel_flow = client.search.find_flow(['steel'])

    if steel_flow:
        print(f"Found: {steel_flow.name}")

        # Find who produces it
        provider = client.search.find_best_provider(steel_flow)
        if provider:
            print(f"Provider: {provider.name}")
    else:
        print("Steel not found in database")
```

**What's happening here:**
1. `find_flow(['steel'])` searches for flows containing "steel"
2. `find_best_provider()` finds the process that produces this flow
3. We use `with` statement for automatic cleanup

## Step 4: Create a Simple Process

Now let's create our own process:

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Step 1: Find input material
    steel = client.search.find_flow(['steel'])
    steel_provider = client.search.find_best_provider(steel)

    # Step 2: Create output product
    widget = client.data.create_product_flow("Widget", "Our product")

    # Step 3: Create exchanges
    exchanges = [
        # Output: 1 widget (this is what we produce)
        client.data.create_exchange(
            widget,
            amount=1.0,
            is_input=False,
            is_quantitative_reference=True  # Mark as main output
        ),
        # Input: 2 kg of steel
        client.data.create_exchange(
            steel,
            amount=2.0,
            is_input=True,
            provider=steel_provider
        )
    ]

    # Step 4: Create the process
    process = client.data.create_process(
        name="Widget Production",
        description="Produces 1 widget from 2 kg steel",
        exchanges=exchanges
    )

    print(f"✓ Created process: {process.name}")
    print(f"  Process ID: {process.id}")
```

**Congratulations!** You've created your first process in openLCA.

You can now open openLCA and see your new "Widget Production" process in the database.

## Step 5: Run a Calculation

Let's calculate the environmental impact of producing 1 widget:

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Find our widget process (created in Step 4)
    widget_process = client.search.find_processes(['Widget Production'])
    if not widget_process:
        print("Widget Production process not found - run Step 4 first")
        exit(1)

    process_ref = widget_process[0]

    # Create a product system
    system = client.systems.create_product_system(process_ref)
    print(f"✓ Created product system: {system.name}")

    # Find an impact method (e.g., TRACI)
    method = client.search.find_impact_method(['TRACI'])
    if not method:
        print("TRACI method not found - install TRACI method pack")
        exit(1)

    print(f"✓ Using impact method: {method.name}")

    # Calculate!
    result = client.calculate.simple_calculation(system, method)
    print("✓ Calculation complete")

    # Get total impacts
    impacts = client.results.get_total_impacts(result)

    # Print results
    print("\nEnvironmental Impacts:")
    print("-" * 60)
    for impact in impacts[:5]:  # Show first 5 impacts
        name = impact['name']
        amount = impact['amount']
        unit = impact['unit']
        print(f"{name:40} {amount:12.4e} {unit}")

    # IMPORTANT: Always dispose results
    result.dispose()
    print("\n✓ Results disposed")
```

**Expected output:**
```
✓ Created product system: Widget Production
✓ Using impact method: TRACI 2.1
✓ Calculation complete

Environmental Impacts:
------------------------------------------------------------
Acidification                                  1.2345e-03 mol H+ eq
Global warming                                 2.3456e+00 kg CO2 eq
Eutrophication                                 3.4567e-04 kg N eq
Ozone depletion                                4.5678e-08 kg CFC-11 eq
Smog                                           5.6789e-02 kg O3 eq

✓ Results disposed
```

## Step 6: Contribution Analysis

Find out what contributes most to the impacts:

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Get widget process and create system
    widget_process = client.search.find_processes(['Widget Production'])[0]
    system = client.systems.create_product_system(widget_process)

    # Get impact method
    method = client.search.find_impact_method(['TRACI'])

    # Run calculation
    result = client.calculate.simple_calculation(system, method)

    # Get impacts
    impacts = client.results.get_total_impacts(result)

    # Analyze top contributors for Global Warming
    gwp_impact = next(
        (imp for imp in impacts if 'warming' in imp['name'].lower()),
        None
    )

    if gwp_impact:
        print(f"\nTop contributors to {gwp_impact['name']}:")
        print("-" * 60)

        contributors = client.contributions.get_top_contributors(
            result,
            gwp_impact['category'],
            n=5  # Top 5
        )

        for i, contrib in enumerate(contributors, 1):
            print(f"{i}. {contrib.name}")
            print(f"   Contribution: {contrib.share*100:.1f}%")
            print(f"   Amount: {contrib.amount:.4e} {gwp_impact['unit']}")
            print()

    # Cleanup
    result.dispose()
```

## Step 7: Deeper Analysis (new in v0.4)

Once you have a `result`, v0.4 adds richer result helpers:

```python
with OLCAClient(port=8080) as client:
    system = client.systems.create_product_system(
        client.search.find_processes(['Widget Production'])[0]
    )
    method = client.search.find_impact_method(['TRACI'])
    result = client.calculate.simple_calculation(system, method)
    try:
        impacts = client.results.get_total_impacts(result)
        gwp = next(i for i in impacts if 'warming' in i['name'].lower())
        cat = gwp['category']

        # Contribution (hotspot) TREE — upstream, recursive
        tree = client.contributions.get_contribution_tree(
            result, cat, max_depth=3, min_share=0.01
        )
        for node in tree:
            print(f"{node.name}: {node.share*100:.1f}%")
            for child in node.children:
                print(f"   └─ {child.name}: {child.share*100:.1f}%")

        # Full life cycle inventory (elementary flows)
        inventory = client.results.get_inventory(result, direction='output')

        # Normalized & weighted impacts (if the method defines them)
        normalized = client.results.get_normalized_impacts(result)
        weighted = client.results.get_weighted_impacts(result)

        # Sankey data (viz / MCP friendly dict)
        sankey = client.results.get_sankey(result, cat, max_nodes=50)

        # Reliability self-check
        from openlca_ipc import check_result_consistency
        for warning in check_result_consistency(result):
            print("⚠", warning)
    finally:
        result.dispose()
```

### Structured responses for agents / MCP

```python
from openlca_ipc import OLCAClient, ResultSummary, CalculationContext, health_check

with OLCAClient(port=8080) as client:
    print(health_check(client))  # connection + entity counts

    system = client.systems.create_product_system(
        client.search.find_processes(['Widget Production'])[0]
    )
    method = client.search.find_impact_method(['TRACI'])
    result = client.calculate.simple_calculation(system, method)
    try:
        impacts = client.results.get_total_impacts(result)
        summary = ResultSummary.from_impacts(
            impacts, database="my_db", impact_method=method, top_n=5
        )
        print(summary.to_json())   # compact JSON for an LLM/MCP tool

        # Provenance for reproducible artifacts
        context = CalculationContext.capture(
            database="my_db", server_port=8080,
            product_system=system, impact_method=method,
        )
        print(context.to_dict())
    finally:
        result.dispose()
```

See **[Agent & MCP usage](agent-usage.md)** for the full structured-response, reproducibility, and error-handling guide.

## Common Patterns

### Pattern 1: Context Manager (Recommended)

```python
from openlca_ipc import OLCAClient

# Connection automatically managed
with OLCAClient(port=8080) as client:
    # Do work here
    flow = client.search.find_flow(['steel'])
    # Connection automatically closed when done
```

### Pattern 2: Explicit Connection

```python
from openlca_ipc import OLCAClient

# Manual connection management
client = OLCAClient(port=8080)
flow = client.search.find_flow(['steel'])
# The underlying olca_ipc.Client holds no OS resources to close; the context
# manager (Pattern 1) is still preferred for symmetry. Always dispose *results*.
```

### Pattern 2b: Read-only (safe) mode

```python
from openlca_ipc import OLCAClient
from openlca_ipc.agent import WriteBlocked

# Safe mode: reads/searches/calculations work, but any write raises.
with OLCAClient(port=8080, read_only=True) as client:
    flow = client.search.find_flow(['steel'])      # OK
    try:
        client.data.create_product_flow("Widget")  # blocked
    except WriteBlocked as e:
        print(e.to_dict())  # structured, recoverable error envelope
```

### Pattern 3: Always Dispose Results

```python
with OLCAClient(port=8080) as client:
    result = client.calculate.simple_calculation(system, method)

    try:
        # Process results
        impacts = client.results.get_total_impacts(result)
        # ... do analysis ...
    finally:
        result.dispose()  # ALWAYS dispose, even if error occurs
```

### Pattern 4: Check Before Using

```python
with OLCAClient(port=8080) as client:
    # Always check search results
    steel = client.search.find_flow(['steel'])
    if not steel:
        print("Steel not found!")
        return

    provider = client.search.find_best_provider(steel)
    if not provider:
        print("No provider found!")
        return

    # Now safe to use
    exchange = client.data.create_exchange(
        steel, 1.0, is_input=True, provider=provider
    )
```

## Complete Example: Full LCA Workflow

Here's a complete example putting it all together:

```python
from openlca_ipc import OLCAClient

def main():
    """Complete LCA workflow example."""

    with OLCAClient(port=8080) as client:
        print("1. Searching for materials...")
        steel = client.search.find_flow(['steel'])
        aluminum = client.search.find_flow(['aluminum'])

        if not steel or not aluminum:
            print("Required materials not found!")
            return

        steel_provider = client.search.find_best_provider(steel)
        aluminum_provider = client.search.find_best_provider(aluminum)

        print("✓ Found materials and providers")

        print("\n2. Creating product...")
        car_part = client.data.create_product_flow(
            "Car Part",
            "Mixed metal component"
        )

        print("\n3. Creating process...")
        exchanges = [
            client.data.create_exchange(
                car_part, 1.0, is_input=False, is_quantitative_reference=True
            ),
            client.data.create_exchange(
                steel, 5.0, is_input=True, provider=steel_provider
            ),
            client.data.create_exchange(
                aluminum, 2.0, is_input=True, provider=aluminum_provider
            )
        ]

        process = client.data.create_process(
            "Car Part Manufacturing",
            exchanges=exchanges
        )
        print(f"✓ Created process: {process.name}")

        print("\n4. Creating product system...")
        system = client.systems.create_product_system(process.to_ref())
        print(f"✓ Created system: {system.name}")

        print("\n5. Finding impact method...")
        method = client.search.find_impact_method(['TRACI'])
        if not method:
            print("TRACI not found - skipping calculation")
            return
        print(f"✓ Using method: {method.name}")

        print("\n6. Calculating impacts...")
        result = client.calculate.simple_calculation(system, method)
        print("✓ Calculation complete")

        print("\n7. Results:")
        print("=" * 70)
        impacts = client.results.get_total_impacts(result)
        for impact in impacts:
            print(f"{impact['name']:40} {impact['amount']:12.4e} {impact['unit']}")

        print("\n8. Cleaning up...")
        result.dispose()
        print("✓ Done!")

if __name__ == "__main__":
    main()
```

Save this as `complete_example.py` and run:
```bash
python complete_example.py
```

## Next Steps

Now that you've got the basics:

1. **[Tutorials](tutorials/README.md)** - In-depth step-by-step guides
2. **[API Reference](api/README.md)** - Complete API documentation
3. **[Examples](../examples/)** - More working examples
4. **[Advanced Usage](advanced-usage.md)** - Advanced patterns and techniques

## Quick Reference Card

```python
# Import
from openlca_ipc import OLCAClient

# Connect
with OLCAClient(port=8080) as client:

    # Search
    flow = client.search.find_flow(['keyword'])
    provider = client.search.find_best_provider(flow)
    method = client.search.find_impact_method(['TRACI'])

    # Create
    product = client.data.create_product_flow("Name")
    exchange = client.data.create_exchange(flow, amount, is_input, provider)
    process = client.data.create_process("Name", exchanges=[...])

    # Calculate
    system = client.systems.create_product_system(process)
    result = client.calculate.simple_calculation(system, method)

    # Analyze
    impacts = client.results.get_total_impacts(result)
    contributors = client.contributions.get_top_contributors(result, impact, n=5)

    # Export
    client.export.export_to_csv(impacts, 'results.csv')

    # Cleanup
    result.dispose()
```

## Common Issues

**Q: "Connection failed" error**
- Make sure openLCA is running
- Make sure IPC server is started
- Check port number matches

**Q: "Material not found" error**
- Material may not be in your database
- Try different keywords
- Use broader search: `find_flows(['steel'], max_results=10)`

**Q: "No provider found" error**
- Flow may be an elementary flow (no provider needed)
- Database may not have production processes
- Check flow type

## Getting Help

- **Documentation**: [Full docs](../documentation/index.md)
- **Examples**: [Example scripts](../examples/)
- **Issues**: [GitHub Issues](https://github.com/SDAI-institute/openlca-ipc/issues)
- **Email**: dernestbanksch@gmail.com
