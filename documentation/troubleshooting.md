# Troubleshooting Guide

This guide helps you diagnose and fix common problems when using the openLCA IPC Python library.

## Connection Problems

### Problem: ConnectionError on Client Initialization

```python
ConnectionError: Could not connect to openLCA IPC server on port 8080
```

**Diagnostic Steps:**

1. **Check if openLCA is running:**
   - Look for openLCA in your running applications
   - If not running, launch it

2. **Check if a database is open:**
   - In openLCA: File → Open Database
   - Wait for it to fully load

3. **Check if IPC server is started:**
   - In openLCA: Tools → Developer Tools → IPC Server
   - Look for "Started" status
   - If showing "Stopped", click "Start"

4. **Verify port number:**
   ```python
   # Check IPC server window for actual port
   client = OLCAClient(port=8080)  # Must match!
   ```

5. **Test with telnet (optional):**
   ```bash
   telnet localhost 8080
   ```
   If this fails, IPC server isn't running properly.

**Solutions:**

```python
# Solution 1: Restart IPC server
# 1. In openLCA, stop IPC server
# 2. Close IPC server window
# 3. Reopen: Tools → Developer Tools → IPC Server
# 4. Click Start
# 5. Try connecting again

# Solution 2: Restart openLCA
# 1. Close openLCA completely
# 2. Reopen openLCA
# 3. Open database
# 4. Start IPC server
# 5. Try connecting again

# Solution 3: Check firewall
# Ensure localhost connections are allowed
# Try temporarily disabling firewall to test

# Solution 4: Try different port
# In IPC server window, change port to 9000
client = OLCAClient(port=9000)
```

---

### Problem: test_connection() Returns False

```python
client = OLCAClient(port=8080)  # No error
print(client.test_connection())  # False
```

**Diagnostic:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = OLCAClient(port=8080)
result = client.test_connection()
# Check console for error messages
```

**Common Causes:**

1. **Database not fully loaded**
   - Wait for database to finish loading
   - Try again after 30 seconds

2. **IPC server crashed**
   - Restart IPC server in openLCA

3. **Database corrupted**
   - Try opening different database
   - If problem persists, reinstall openLCA

**Solution:**

```python
import time

client = OLCAClient(port=8080)

# Retry connection test
for i in range(5):
    if client.test_connection():
        print("Connected!")
        break
    print(f"Attempt {i+1}/5 failed, retrying...")
    time.sleep(2)
else:
    print("Connection failed after 5 attempts")
    print("Try restarting openLCA and IPC server")
```

---

## Search Problems

### Problem: find_flow() Returns None

```python
steel = client.search.find_flow(['steel'])
print(steel)  # None
```

**Diagnostic:**

```python
# Check if ANY flows exist
all_flows = client.client.get_descriptors(o.Flow)
print(f"Total flows in database: {len(all_flows)}")

if len(all_flows) == 0:
    print("Database is empty or not loaded properly")
else:
    # Check first 10 flows
    print("\nFirst 10 flows:")
    for flow in all_flows[:10]:
        print(f"  - {flow.name}")
```

**Solutions:**

1. **Try broader keywords:**
```python
# Instead of very specific
steel = client.search.find_flow(['steel', 'hot', 'rolled', 'coil'])

# Try broader
steel = client.search.find_flow(['steel'])
```

2. **Check all matches:**
```python
steels = client.search.find_flows(['steel'], max_results=20)
print(f"Found {len(steels)} matches:")
for i, s in enumerate(steels, 1):
    print(f"{i}. {s.name}")
```

3. **Try alternative spellings:**
```python
material = client.search.find_flow(['aluminum'])
if not material:
    material = client.search.find_flow(['aluminium'])
if not material:
    material = client.search.find_flow(['Al'])
```

4. **Case-insensitive manual search:**
```python
def find_flow_fuzzy(client, name_part):
    """Find flow with very flexible matching."""
    name_lower = name_part.lower()
    for flow in client.client.get_descriptors(o.Flow):
        if name_lower in flow.name.lower():
            return flow
    return None

steel = find_flow_fuzzy(client, 'steel')
```

---

### Problem: find_best_provider() Returns None

```python
flow = client.search.find_flow(['steel'])
provider = client.search.find_best_provider(flow)
print(provider)  # None
```

**Diagnostic:**

```python
# Check flow type
flow = client.search.find_flow(['material'])
full_flow = client.client.get(o.Flow, flow.id)
print(f"Flow type: {full_flow.flow_type}")

# Check if providers exist
providers = client.search.find_providers(flow)
print(f"Number of providers: {len(providers)}")
```

**Common Causes:**

1. **Flow is elementary** (CO2, water, etc.):
```python
if full_flow.flow_type == o.FlowType.ELEMENTARY_FLOW:
    print("Elementary flows don't have providers")
    # Don't set provider for elementary flows
```

2. **No production processes in database:**
```python
# Your database may not have processes that produce this flow
# Solution: Use different database or create provider process
```

3. **Flow is waste:**
```python
if full_flow.flow_type == o.FlowType.WASTE_FLOW:
    print("Waste flows may not have providers")
```

**Solution:**

```python
flow = client.search.find_flow(['steel'])
provider = client.search.find_best_provider(flow)

if not provider:
    # Check why
    full_flow = client.client.get(o.Flow, flow.id)

    if full_flow.flow_type == o.FlowType.ELEMENTARY_FLOW:
        print("Elementary flow - no provider needed")
        # Create exchange without provider
        exchange = client.data.create_exchange(
            flow, 1.0, is_input=True
            # No provider parameter
        )
    else:
        print("No provider found - check database")
        # Create provider process or use different database
```

---

## Calculation Problems

### Problem: All Impact Values Are Zero

```python
impacts = client.results.get_total_impacts(result)
for impact in impacts:
    print(impact['amount'])  # All 0.0
```

**Diagnostic:**

```python
# Check inventory results
inventory = client.results.get_inventory_results(result)
print(f"Inventory entries: {len(inventory)}")

if len(inventory) == 0:
    print("No inventory - problem with product system")
else:
    print("First 5 inventory items:")
    for item in inventory[:5]:
        print(f"  {item['flow']}: {item['amount']}")
```

**Common Causes & Solutions:**

1. **Missing providers:**
```python
# Problem: Exchanges without providers
exchange = client.data.create_exchange(
    steel, 1.0, is_input=True
    # Missing provider!
)

# Solution: Add providers
provider = client.search.find_best_provider(steel)
exchange = client.data.create_exchange(
    steel, 1.0, is_input=True, provider=provider
)
```

2. **Product system not auto-completed:**
```python
# After creating product system
system = client.systems.create_product_system(process)

# Auto-complete to build supply chain
completed_system = client.client.get(o.ProductSystem, system.id)
# Check if all processes are included
print(f"Processes in system: {len(completed_system.process_refs)}")
```

3. **Wrong impact method:**
```python
# Your flows may not have characterization factors for this method
# Try different method
traci = client.search.find_impact_method(['TRACI'])
recipe = client.search.find_impact_method(['ReCiPe'])

# Calculate with both and compare
```

4. **Quantitative reference not set:**
```python
# Make sure one exchange is marked as quantitative reference
exchanges = [
    client.data.create_exchange(
        product, 1.0,
        is_input=False,
        is_quantitative_reference=True  # Must have this!
    ),
    # ... other exchanges ...
]
```

---

### Problem: "Result object has no attribute 'amount'"

```python
AttributeError: 'EnviFlow' object has no attribute 'amount'
```

**Cause:**
Different olca-ipc versions use different attribute names (`amount` vs `value`).

**Solution:**
The library handles this automatically, but if you're accessing results directly:

```python
# Instead of:
amount = envi_flow.amount

# Use:
amount = getattr(envi_flow, 'amount', None) or getattr(envi_flow, 'value', None)
```

Or just use the library methods:
```python
# Library handles version differences
impacts = client.results.get_total_impacts(result)
# This works regardless of olca-ipc version
```

---

### Problem: Calculation Takes Forever

```python
result = client.calculate.simple_calculation(system, method)
# Hangs for hours...
```

**Diagnostic:**

```python
import time

start = time.time()
result = client.calculate.simple_calculation(system, method)
elapsed = time.time() - start
print(f"Calculation took {elapsed:.1f} seconds")
```

**Common Causes:**

1. **Very large product system:**
```python
# Check system size
system_full = client.client.get(o.ProductSystem, system.id)
print(f"Processes: {len(system_full.process_refs)}")
print(f"Links: {len(system_full.process_links)}")

# If thousands of processes, calculation will be slow
```

2. **Circular references:**
```python
# Check for circular dependencies in your product system
# May need to manually fix system structure
```

**Solutions:**

1. **Simplify system:**
   - Use aggregated processes
   - Reduce system boundaries

2. **Use faster computer:**
   - More RAM helps
   - Faster CPU helps

3. **Close other applications:**
   - Free up RAM and CPU

4. **Show progress:**
```python
import time
from threading import Thread

def show_progress():
    """Show that calculation is running."""
    start = time.time()
    while calculating:
        elapsed = time.time() - start
        print(f"\rCalculating... {elapsed:.0f}s", end='')
        time.sleep(1)

calculating = True
progress_thread = Thread(target=show_progress)
progress_thread.start()

result = client.calculate.simple_calculation(system, method)

calculating = False
progress_thread.join()
print("\n✓ Calculation complete!")
```

---

## Data Creation Problems

### Problem: "Flow property 'Mass' not found"

```python
ValueError: Mass flow property not found in database
```

**Cause:**
Database is missing the Mass flow property.

**Solutions:**

1. **Use complete database:**
   - Download from [Nexus](https://nexus.openlca.org/databases)
   - Or create new database in openLCA (it will have Mass)

2. **Check database:**
```python
# List flow properties
props = client.client.get_descriptors(o.FlowProperty)
print("Flow properties in database:")
for prop in props:
    print(f"  - {prop.name}")
```

---

### Problem: Process Has No Quantitative Reference

```python
# Process created but can't be used
```

**Diagnostic:**

```python
# Check process
process = client.client.get(o.Process, process_id)
qref = process.quantitative_reference

if not qref:
    print("No quantitative reference set!")
```

**Solution:**

```python
# Make sure one exchange is marked as quantitative reference
exchanges = [
    client.data.create_exchange(
        product,
        amount=1.0,
        is_input=False,
        is_quantitative_reference=True  # This!
    ),
    # ... other exchanges ...
]
```

---

## Memory Problems

### Problem: Memory Usage Grows

**Cause:**
Not disposing calculation results.

**Solution:**

```python
# Bad - memory leak
results = []
for i in range(100):
    result = client.calculate.simple_calculation(system, method)
    impacts = client.results.get_total_impacts(result)
    results.append(impacts)
    # Never disposed!

# Good - proper cleanup
results = []
for i in range(100):
    result = client.calculate.simple_calculation(system, method)
    try:
        impacts = client.results.get_total_impacts(result)
        results.append(impacts)
    finally:
        result.dispose()  # Always dispose
```

---

## Import Errors

### Problem: "No module named 'openlca_ipc'"

```python
ImportError: No module named 'openlca_ipc'
```

**Solutions:**

1. **Check installation:**
```bash
pip list | grep openlca
# Should see openlca-ipc
```

2. **Reinstall:**
```bash
cd openlca-ipc
pip install -e . --force-reinstall
```

3. **Check Python environment:**
```bash
which python
which pip
# Make sure using correct environment
```

---

### Problem: "No module named 'pandas'" (or scipy, matplotlib)

```python
ModuleNotFoundError: No module named 'pandas'
```

**Solution:**

```bash
# Install optional dependencies
pip install "openlca-ipc[full]"

# Or install individually
pip install pandas scipy matplotlib
```

---

## Debugging Tips

### Enable Logging

```python
import logging

# See what the library is doing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or more detailed
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Objects

```python
# Check what you got
flow = client.search.find_flow(['steel'])
print(f"Type: {type(flow)}")
print(f"ID: {flow.id}")
print(f"Name: {flow.name}")
print(f"All attributes: {dir(flow)}")
```

### Use Python Debugger

```python
import pdb

# Start debugging at specific point
pdb.set_trace()

# Step through code
# Commands: n (next), s (step), c (continue), p var (print)
```

### Check openLCA Console

In openLCA, check the console (View → Console) for error messages from the IPC server.

## Still Having Problems?

1. **Check documentation:**
   - [FAQ](../documentation/faq.md)
   - [API Reference](api/README.md)
   - [Examples](../examples/)

2. **Search existing issues:**
   - [GitHub Issues](https://github.com/dernestbank/openlca-ipc/issues)

3. **Create new issue:**
   - Include error message
   - Include minimal code to reproduce
   - Include environment (OS, Python version, openLCA version)

4. **Contact:**
   - Email: dernestbanksch@gmail.com

## Reporting Bugs

When reporting bugs, include:

```python
# 1. Code that reproduces the problem
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Minimal code that shows the problem
    pass

# 2. Error message (full traceback)

# 3. Environment info
import sys
import olca_ipc
import olca_schema

print(f"Python: {sys.version}")
print(f"olca-ipc: {olca_ipc.__version__}")
print(f"olca-schema: {olca_schema.__version__}")
print(f"OS: {sys.platform}")

# 4. openLCA version
# (from openLCA: Help → About)
```

This information helps diagnose and fix issues quickly.
