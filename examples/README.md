# Examples

This folder contains working examples demonstrating how to use the openLCA IPC Python library.

## Prerequisites

Before running examples:

1. ✓ Install the library (see [Installation Guide](../documentation/installation.md))
2. ✓ openLCA desktop running
3. ✓ Database loaded in openLCA
4. ✓ IPC server started (Tools → Developer Tools → IPC Server)

## Available Examples

### Basic Examples

#### `test_package.py`
Basic package functionality test and demonstrations.

**What it shows:**
- Connecting to openLCA
- Testing connection
- Basic search operations
- Finding flows and providers

**Run:**
```bash
python examples/test_package.py
```

#### `utils_examples.py`
Basic utility functions and common patterns.

**What it shows:**
- Search utilities
- Data creation
- Basic workflow patterns

**Run:**
```bash
python examples/utils_examples.py
```

### Intermediate Examples

#### `working_demo.py`
Complete working demonstration of a full LCA workflow.

**What it shows:**
- Complete LCA workflow from start to finish
- Searching for materials
- Creating processes
- Building product systems
- Running calculations
- Analyzing results
- Proper cleanup

**Run:**
```bash
python examples/working_demo.py
```

**Expected output:**
```
1. Connecting to openLCA...
✓ Connected successfully

2. Searching for materials...
✓ Found steel: steel production
✓ Found aluminum: aluminum production

3. Creating product...
✓ Created product: Widget

4. Creating process...
✓ Created process: Widget Production

5. Running calculation...
✓ Calculation complete

6. Results:
Global warming: 1.2345e+01 kg CO2 eq
Acidification: 2.3456e-02 mol H+ eq
...

✓ Cleanup complete
```

### Advanced Examples

#### `utils_example2Advanced.py`
Advanced usage patterns and techniques.

**What it shows:**
- Advanced search strategies
- Complex data creation
- Parameter management
- Contribution analysis
- Uncertainty analysis
- Export functionality

**Run:**
```bash
python examples/utils_example2Advanced.py
```

#### `example-complete.py`
Comprehensive example covering all major features.

**What it shows:**
- All library modules
- Error handling
- Best practices
- Real-world patterns

**Run:**
```bash
python examples/example-complete.py
```

### Legacy/Reference Examples

#### `ipc_from_scratch.py`
Shows how to use raw olca-ipc vs this library.

**What it shows:**
- Comparison between raw olca-ipc and this library
- Low-level IPC operations
- Why this library makes things easier

**Purpose:**
Educational - shows the difference between low-level and high-level APIs.

#### `test-pet-pc.py`
PET vs PC bottle comparison example.

**What it shows:**
- Comparative LCA
- Working with real materials
- Results comparison
- Practical LCA workflow

**Run:**
```bash
python examples/test-pet-pc.py
```

**Note:** Requires specific materials in database (PET, PC, etc.)

## Running Examples

### Method 1: Direct Execution

```bash
# From project root
python examples/working_demo.py
```

### Method 2: As Module

```bash
# From project root
python -m examples.working_demo
```

### Method 3: Interactive

```python
# Start Python in project root
>>> from examples import working_demo
>>> # Explore the code
```

## Modifying Examples

Feel free to modify examples to match your use case:

1. **Change materials:**
```python
# In any example, change search keywords
steel = client.search.find_flow(['steel'])
# Change to:
copper = client.search.find_flow(['copper'])
```

2. **Change amounts:**
```python
# Adjust exchange amounts
exchange = client.data.create_exchange(
    steel,
    amount=2.0,  # Change this
    is_input=True
)
```

3. **Change impact method:**
```python
# Use different method
method = client.search.find_impact_method(['TRACI'])
# Change to:
method = client.search.find_impact_method(['ReCiPe'])
```

## Common Example Patterns

### Pattern 1: Basic Workflow

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # 1. Search
    material = client.search.find_flow(['material name'])

    # 2. Create
    product = client.data.create_product_flow("Product")

    # 3. Calculate
    # ... create process, system, etc.

    # 4. Analyze
    # ... get results
```

### Pattern 2: Error Handling

```python
with OLCAClient(port=8080) as client:
    material = client.search.find_flow(['material'])
    if not material:
        print("Material not found!")
        return

    provider = client.search.find_best_provider(material)
    if not provider:
        print("No provider found!")
        return

    # Safe to use
```

### Pattern 3: Resource Cleanup

```python
with OLCAClient(port=8080) as client:
    result = client.calculate.simple_calculation(system, method)
    try:
        impacts = client.results.get_total_impacts(result)
        # ... use impacts ...
    finally:
        result.dispose()  # Always dispose
```

## Creating Your Own Examples

Template for new examples:

```python
"""
Example: [Description]

This example demonstrates:
- Point 1
- Point 2
- Point 3
"""

from openlca_ipc import OLCAClient

def main():
    """Main example function."""
    print("Starting example...")

    with OLCAClient(port=8080) as client:
        # Test connection
        if not client.test_connection():
            print("Failed to connect to openLCA")
            return

        print("✓ Connected to openLCA")

        # Your example code here
        try:
            run_example(client)
            print("\n✓ Example completed successfully")
        except Exception as e:
            print(f"\n✗ Example failed: {e}")

def run_example(client):
    """Run the example logic."""
    # Implementation here
    pass

if __name__ == "__main__":
    main()
```

## Troubleshooting Examples

### Example Won't Run

**Check:**
1. Is openLCA running?
2. Is database loaded?
3. Is IPC server started?
4. Is library installed?

```bash
# Verify installation
pip list | grep openlca
```

### Material Not Found

**Solutions:**
1. Check if material exists in your database
2. Try different keywords
3. List available materials:
```python
all_flows = client.client.get_descriptors(o.Flow)
for flow in all_flows[:20]:
    print(flow.name)
```

### Import Error

**Solution:**
```bash
# From project root, install in editable mode
pip install -e .
```

### Connection Error

**Solution:**
```python
# Check port matches IPC server
client = OLCAClient(port=8080)  # Default port

# Try test connection
if not client.test_connection():
    print("Connection failed - check IPC server")
```

## Example Output

Most examples produce output like:

```
Starting example...
✓ Connected to openLCA

1. Searching for materials...
Found: steel production
Found: aluminum production

2. Creating process...
✓ Created: Widget Production

3. Running calculation...
✓ Calculation complete

4. Results:
Global warming: 1.23e+01 kg CO2 eq
Acidification: 2.34e-02 mol H+ eq
Eutrophication: 3.45e-03 kg N eq

✓ Example completed successfully
```

## Learning Path

Recommended order to explore examples:

1. **Start with:** `test_package.py`
   - Basic functionality
   - Connection testing
   - Simple searches

2. **Then:** `working_demo.py`
   - Complete workflow
   - Understand the full process

3. **Next:** `utils_examples.py`
   - Common patterns
   - Utility functions

4. **Advanced:** `utils_example2Advanced.py`
   - Advanced features
   - Complex scenarios

5. **Reference:** `example-complete.py`
   - Comprehensive coverage
   - All features

## Additional Resources

- **[Quick Start Guide](../docs/quickstart.md)** - Get started quickly
- **[API Reference](../docs/api/README.md)** - Detailed API docs
- **[Tutorials](../docs/tutorials/README.md)** - Step-by-step guides
- **[Best Practices](../documentation/best-practices.md)** - Recommended patterns
- **[Troubleshooting](../documentation/troubleshooting.md)** - Common issues
- **[FAQ](../documentation/faq.md)** - Frequently asked questions

## Contributing Examples

Have a useful example? Contribute it!

1. Create example file in `examples/`
2. Add documentation at the top
3. Follow the template above
4. Test it works
5. Update this README
6. Submit pull request

## Getting Help

If examples don't work:

1. Check [Troubleshooting Guide](../documentation/troubleshooting.md)
2. Search [GitHub Issues](https://github.com/dernestbank/openlca-ipc/issues)
3. Create new issue with:
   - Which example
   - Error message
   - Your environment
4. Email: dernestbanksch@gmail.com

## License

Examples are part of the openlca-ipc library and are licensed under the MIT License.
