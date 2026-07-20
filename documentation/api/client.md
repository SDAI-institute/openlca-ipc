# OLCAClient API Reference

## Class: `OLCAClient`

Main client wrapper for openLCA IPC operations. Provides organized access to all utility modules through a single interface.

### Constructor

```python
OLCAClient(port: int = 8080)
```

Initialize the openLCA client and connect to the IPC server.

**Parameters:**
- `port` (int, optional): IPC server port. Default: 8080.

**Raises:**
- `ConnectionError`: If unable to connect to the IPC server.

**Example:**
```python
from openlca_ipc import OLCAClient

# Basic connection
client = OLCAClient(port=8080)

# Custom port
client = OLCAClient(port=9000)
```

### Attributes

After initialization, the client provides access to specialized utility modules:

| Attribute | Type | Description |
|-----------|------|-------------|
| `client` | `ipc.Client` | Underlying olca-ipc client |
| `search` | `SearchUtils` | Search and discovery utilities |
| `data` | `DataBuilder` | Data creation utilities |
| `systems` | `SystemBuilder` | Product system management |
| `calculate` | `CalculationManager` | Calculation execution |
| `results` | `ResultsAnalyzer` | Results analysis |
| `contributions` | `ContributionAnalyzer` | Contribution analysis |
| `uncertainty` | `UncertaintyAnalyzer` | Uncertainty analysis |
| `parameters` | `ParameterManager` | Parameter management |
| `export` | `ExportManager` | Export utilities |

### Methods

#### `test_connection()`

Test if the connection to openLCA is working.

**Returns:**
- `bool`: True if connection is successful, False otherwise.

**Example:**
```python
client = OLCAClient(port=8080)
if client.test_connection():
    print("Connected successfully!")
else:
    print("Connection failed - check if IPC server is running")
```

### Context Manager Support

The `OLCAClient` can be used as a context manager for automatic connection cleanup:

```python
with OLCAClient(port=8080) as client:
    # Do work...
    flows = client.search.find_flows(['steel'])
    # Connection automatically closed when exiting the block
```

**Methods:**
- `__enter__()`: Returns self
- `__exit__()`: Automatically closes the IPC connection

### Usage Patterns

#### Basic Usage

```python
from openlca_ipc import OLCAClient

# Connect to openLCA
client = OLCAClient(port=8080)

# Test connection
if not client.test_connection():
    print("Failed to connect to openLCA")
    exit(1)

# Use the client
flow = client.search.find_flow(['steel'])
print(f"Found: {flow.name}")
```

#### Context Manager (Recommended)

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Connection is automatically managed
    steel = client.search.find_flow(['steel'])
    provider = client.search.find_best_provider(steel)

    # Create process
    product = client.data.create_product_flow("My Product")
    exchanges = [
        client.data.create_exchange(product, 1.0, is_input=False, is_quantitative_reference=True),
        client.data.create_exchange(steel, 2.0, is_input=True, provider=provider)
    ]
    process = client.data.create_process("My Process", exchanges=exchanges)

# Connection automatically closed here
```

#### Error Handling

```python
from openlca_ipc import OLCAClient

try:
    client = OLCAClient(port=8080)
except ConnectionError as e:
    print(f"Failed to connect: {e}")
    print("Make sure:")
    print("1. openLCA is running")
    print("2. IPC server is started (Tools → Developer Tools → IPC Server)")
    print("3. Port 8080 is not blocked by firewall")
    exit(1)

# Test connection
if not client.test_connection():
    print("Connection test failed")
    exit(1)

# Proceed with operations
try:
    flow = client.search.find_flow(['material'])
    if not flow:
        print("Material not found in database")
except Exception as e:
    print(f"Error during operation: {e}")
```

### Module Access Examples

Once connected, access specialized functionality through module attributes:

```python
with OLCAClient(port=8080) as client:
    # Search operations
    steel_flow = client.search.find_flow(['steel'])
    impact_method = client.search.find_impact_method(['TRACI'])

    # Data creation
    product = client.data.create_product_flow("Widget")
    process = client.data.create_process("Widget Production")

    # System building
    system = client.systems.create_product_system(process)

    # Calculations
    result = client.calculate.simple_calculation(system, impact_method)

    # Results analysis
    impacts = client.results.get_total_impacts(result)

    # Contribution analysis
    top_contributors = client.contributions.get_top_contributors(
        result,
        impacts[0]['category'],
        n=5
    )

    # Export
    client.export.export_to_csv(impacts, 'results.csv')

    # Cleanup
    result.dispose()
```

## Connection Prerequisites

Before creating an `OLCAClient`, ensure:

1. **openLCA Desktop is Running**
   - Launch the openLCA desktop application

2. **IPC Server is Started**
   - Go to: Tools → Developer Tools → IPC Server
   - Click "Start"
   - Note the port number (default: 8080)

3. **Firewall Allows Connection**
   - Ensure port 8080 (or your custom port) is not blocked
   - localhost connections should be allowed

## Troubleshooting

### ConnectionError on Initialization

**Problem:**
```python
ConnectionError: Could not connect to openLCA IPC server on port 8080
```

**Solutions:**
1. Verify openLCA is running
2. Start IPC server: Tools → Developer Tools → IPC Server
3. Check port number matches
4. Check firewall settings
5. Try restarting openLCA

### test_connection() Returns False

**Problem:**
```python
client = OLCAClient(port=8080)
print(client.test_connection())  # False
```

**Solutions:**
1. IPC server may have stopped - restart it in openLCA
2. Database may not be loaded - open a database in openLCA
3. Port may be incorrect - verify in IPC server window

## See Also

- [SearchUtils](search.md) - Search and discovery
- [DataBuilder](data.md) - Data creation
- [SystemBuilder](systems.md) - Product systems
- [CalculationManager](calculations.md) - Calculations
- [Quick Start Guide](../quickstart.md) - Getting started tutorial
