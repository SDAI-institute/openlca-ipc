# Frequently Asked Questions (FAQ)

## General Questions

### What is this library?

The openLCA IPC Python library is a high-level wrapper around the olca-ipc protocol that makes it easier to work with openLCA programmatically. It provides simple, Pythonic interfaces for common LCA workflows.

### Do I need the openLCA desktop application?

**Yes.** This library communicates with openLCA through the IPC (Inter-Process Communication) protocol. You need:
- openLCA desktop application installed and running
- A database loaded in openLCA
- The IPC server started

### What versions of openLCA are supported?

- openLCA 2.x is fully supported
- openLCA 1.x may work but is not tested

### Can I use this without the openLCA GUI?

No, the library requires the openLCA desktop application to be running with the IPC server active. The library communicates with openLCA, it doesn't replace it.

### Is this an official openLCA project?

No, this is a community library built on top of the official `olca-ipc` and `olca-schema` libraries from GreenDelta.

## Installation and Setup

### How do I install the library?

Currently, install from source:

```bash
git clone https://github.com/dernestbank/openlca-ipc.git
cd openlca-ipc
pip install -e ".[full]"
```

See the [Installation Guide](../documentation/installation.md) for details.

### What Python version do I need?

Python 3.10 or higher. Check your version:
```bash
python --version
```

### Do I need to install openLCA separately?

Yes, download and install from [openlca.org](https://www.openlca.org/download/).

### Where do I get databases?

- Download from [Nexus](https://nexus.openlca.org/databases)
- Or create your own in openLCA

## Connection Issues

### "ConnectionError: Could not connect to openLCA IPC server"

**Checklist:**
1. ✓ Is openLCA running?
2. ✓ Is a database open?
3. ✓ Is the IPC server started? (Tools → Developer Tools → IPC Server)
4. ✓ Does the port number match? (default: 8080)
5. ✓ Is your firewall blocking localhost connections?

**Solution:**
```python
from openlca_ipc import OLCAClient

# Make sure port matches IPC server
client = OLCAClient(port=8080)

if client.test_connection():
    print("Connected!")
else:
    print("Check the checklist above")
```

### test_connection() returns False

**Possible causes:**
- Database not fully loaded
- IPC server crashed (restart it)
- Wrong port number

**Solution:**
Try restarting the IPC server in openLCA.

### Can I change the port number?

Yes, in the IPC server window in openLCA, change the port, then:
```python
client = OLCAClient(port=9000)  # Use your port
```

## Search and Data

### "Material not found" / find_flow() returns None

**Why:**
- Material doesn't exist in your database
- Keywords don't match
- Spelling differences (aluminum vs aluminium)

**Solutions:**

1. **Try broader keywords:**
```python
# Instead of:
flow = client.search.find_flow(['steel', 'hot', 'rolled'])

# Try:
flow = client.search.find_flow(['steel'])
```

2. **Try alternative spellings:**
```python
flow = client.search.find_flow(['aluminum'])
if not flow:
    flow = client.search.find_flow(['aluminium'])
```

3. **See all matches:**
```python
flows = client.search.find_flows(['steel'], max_results=20)
for i, flow in enumerate(flows):
    print(f"{i+1}. {flow.name}")
```

4. **Check database content:**
```python
# List all flows (first 50)
all_flows = client.client.get_descriptors(o.Flow)
for flow in all_flows[:50]:
    print(flow.name)
```

### How do I search for exact names?

The library uses partial matching. For exact matching:

```python
flows = client.search.find_flows(['exact', 'keywords'])
# Then filter manually
exact_match = next(
    (f for f in flows if f.name == "Exact Name"),
    None
)
```

### What's the difference between find_flow() and find_flows()?

- `find_flow()`: Returns first match (or None)
- `find_flows()`: Returns list of all matches

```python
# Single result
steel = client.search.find_flow(['steel'])

# Multiple results
steels = client.search.find_flows(['steel'], max_results=10)
```

### Why is find_best_provider() returning None?

**Possible reasons:**

1. **Flow is an elementary flow** (no providers):
```python
co2 = client.search.find_flow(['carbon dioxide'])
# CO2 is elementary - no provider needed
```

2. **No production processes in database**:
The database may not have processes that produce this flow.

3. **Flow is a waste flow**:
Waste flows don't have "providers" in the same sense.

**Check flow type:**
```python
flow = client.search.find_flow(['material'])
full_flow = client.client.get(o.Flow, flow.id)
print(f"Flow type: {full_flow.flow_type}")
# PRODUCT_FLOW, ELEMENTARY_FLOW, or WASTE_FLOW
```

## Calculations

### All impact values are zero

**Common causes:**

1. **Missing providers:**
```python
# Bad - no provider
exchange = client.data.create_exchange(
    steel, 1.0, is_input=True
)

# Good - with provider
provider = client.search.find_best_provider(steel)
exchange = client.data.create_exchange(
    steel, 1.0, is_input=True, provider=provider
)
```

2. **Impact method doesn't match flows:**
Your flows may not have characterization factors for this method.

3. **Database missing background data:**
Check if your database has complete supply chains.

### "Result object has no attribute 'value'"

This happens with different olca-ipc versions. The library handles both:

```python
# The library automatically checks both 'amount' and 'value'
impacts = client.results.get_total_impacts(result)
# This works regardless of version
```

### Do I need to dispose results?

**Yes, always!** Results consume memory in openLCA.

```python
result = client.calculate.simple_calculation(system, method)
try:
    impacts = client.results.get_total_impacts(result)
    # ... use results ...
finally:
    result.dispose()  # Always dispose
```

### How long should calculations take?

Depends on:
- Product system complexity
- Database size
- Number of elementary flows
- Your computer speed

Simple systems: seconds
Complex systems: minutes
Monte Carlo (1000 iterations): minutes to hours

## Data Creation

### "Flow property 'Mass' not found"

Your database may be missing the Mass flow property.

**Solution:**
Create a new database or use a complete database from Nexus.

### Can I modify existing processes?

Yes, but carefully:

```python
# Get existing process
process = client.client.get(o.Process, process_id)

# Modify it
process.description = "Updated description"

# Save changes
client.client.put(process)
```

### How do I delete data?

```python
# Delete by ID
client.client.delete(o.Process, process_id)

# Delete by reference
client.client.delete(o.Process, process_ref.id)
```

**Warning:** Deletion is permanent and may break other processes that reference this data!

## Advanced Usage

### Can I run calculations in parallel?

The IPC server handles one calculation at a time. For parallel processing, you'd need multiple openLCA instances on different ports.

### How do I run Monte Carlo simulations?

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    results = client.uncertainty.run_monte_carlo(
        system=my_system,
        impact_method=method,
        iterations=1000
    )

    for impact_name, stats in results.items():
        print(f"{impact_name}:")
        print(f"  Mean: {stats.mean}")
        print(f"  Std Dev: {stats.std}")
```

### Can I export to Excel?

Yes, if you installed with optional dependencies:

```python
# Install pandas
pip install "openlca-ipc[full]"

# Then export
client.export.export_to_excel(impacts, 'results.xlsx')
```

### How do I work with parameters?

```python
# Run scenario analysis
scenarios = client.parameters.run_scenario_analysis(
    system=system,
    impact_method=method,
    parameter_name='distance',
    values=[100, 500, 1000, 5000]
)
```

See [Advanced Usage Guide](advanced-usage.md) for details.

## Performance

### Searches are slow

**Optimizations:**

1. **Limit results:**
```python
flows = client.search.find_flows(['steel'], max_results=5)
```

2. **Use specific flow types:**
```python
products = client.search.find_flows(
    ['steel'],
    flow_type=o.FlowType.PRODUCT_FLOW
)
```

3. **Cache results:**
```python
# Cache frequently used items
steel = client.search.find_flow(['steel'])
# Reuse 'steel' instead of searching again
```

### Calculations are slow

**Normal for:**
- Large product systems
- Complex databases
- Monte Carlo simulations

**Optimizations:**
- Use simpler impact methods
- Reduce system complexity
- Use faster computer
- Close other applications

## Errors and Debugging

### How do I enable logging?

```python
import logging

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now you'll see what's happening
from openlca_ipc import OLCAClient
client = OLCAClient(port=8080)
# Output: "INFO - Connected to openLCA IPC server on port 8080"
```

### How do I see what's being sent to openLCA?

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# You'll see detailed IPC communication
```

### Where can I get help?

1. **Check documentation**: [Full docs](../documentation/index.md)
2. **Search examples**: [Examples folder](../examples/)
3. **GitHub Issues**: [Report bugs](https://github.com/dernestbank/openlca-ipc/issues)
4. **Discussions**: [Ask questions](https://github.com/dernestbank/openlca-ipc/discussions)
5. **Email**: dernestbanksch@gmail.com

## Contributing

### Can I contribute?

Yes! Contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See [Contributing Guide](../CONTRIBUTING.md) for details.

### I found a bug, what should I do?

1. Check if it's already reported in [Issues](https://github.com/dernestbank/openlca-ipc/issues)
2. If not, create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, openLCA version)

### How can I request a feature?

Create a feature request in [GitHub Issues](https://github.com/dernestbank/openlca-ipc/issues) with:
- Use case description
- Why it would be useful
- Proposed API (if you have ideas)

## Migration and Compatibility

### I'm using raw olca-ipc, should I switch?

**Advantages of this library:**
- Simpler, more Pythonic API
- Built-in error handling
- Higher-level utilities
- Better documentation
- Common patterns implemented

**When to use raw olca-ipc:**
- You need low-level control
- You're doing very specific operations
- You have existing code that works

Both can coexist:
```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # High-level operation
    flow = client.search.find_flow(['steel'])

    # Low-level operation when needed
    full_flow = client.client.get(o.Flow, flow.id)
```

### Is this compatible with olca-ipc 2.4.0?

Yes, it's built on top of olca-ipc 2.4.0 and olca-schema 2.4.0.

### Will this work with future openLCA versions?

The library is designed to be forward-compatible, but breaking changes in openLCA may require updates. Check the compatibility notes in releases.

## Best Practices

### What's the recommended way to structure my code?

```python
from openlca_ipc import OLCAClient

def main():
    """Main LCA workflow."""
    with OLCAClient(port=8080) as client:
        # 1. Search
        materials = find_materials(client)

        # 2. Create
        process = create_process(client, materials)

        # 3. Calculate
        results = calculate_impacts(client, process)

        # 4. Analyze
        analyze_results(results)

def find_materials(client):
    """Search for required materials."""
    # ... implementation ...

def create_process(client, materials):
    """Create process from materials."""
    # ... implementation ...

# etc.
```

See [Best Practices Guide](best-practices.md) for more.

### Should I use context managers?

**Yes!** Always use `with` statement:

```python
# Good
with OLCAClient(port=8080) as client:
    # Work here
    pass
# Connection auto-closed

# Less good
client = OLCAClient(port=8080)
# Work here
client.client.close()  # Must remember to close
```

## Still Have Questions?

- **Quickstart**: [Quick Start Guide](quickstart.md)
- **Tutorials**: [Step-by-step guides](tutorials/README.md)
- **API Docs**: [Complete API reference](api/README.md)
- **Examples**: [Working examples](../examples/)
- **Troubleshooting**: [Common issues](troubleshooting.md)
- **Contact**: dernestbanksch@gmail.com
