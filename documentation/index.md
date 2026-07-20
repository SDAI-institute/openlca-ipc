# OpenLCA IPC Python Library - Complete Documentation

Welcome to the comprehensive documentation for the openLCA IPC Python library. This library provides a high-level, Pythonic interface for interacting with openLCA desktop application through the IPC (Inter-Process Communication) protocol.

## Table of Contents

### Getting Started
- [Installation and Setup](installation.md) - Installation instructions, prerequisites, and configuration
- [Quick Start Guide](quickstart.md) - Get up and running in 5 minutes
- [Tutorials](tutorials/README.md) - Step-by-step guides for common workflows

### Core Documentation
- [API Reference](api/README.md) - Complete API documentation for all modules
- [User Guide](user-guide.md) - Comprehensive guide to using the library
- [Examples](../examples/README.md) - Working code examples and use cases

### Advanced Topics
- [Advanced Usage](advanced-usage.md) - Advanced patterns and techniques
- [Uncertainty Analysis](advanced/uncertainty-analysis.md) - Monte Carlo simulations and statistical analysis
- [Contribution Analysis](advanced/contribution-analysis.md) - Process and flow contribution analysis
- [Scenario Analysis](advanced/scenario-analysis.md) - Parameter sensitivity and scenario comparison

### Reference
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [FAQ](faq.md) - Frequently asked questions
- [Best Practices](best-practices.md) - Recommended patterns and practices
- [Migration Guide](migration.md) - Migrating from raw olca-ipc

### Development
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute to this project
- [Development Setup](development.md) - Setting up development environment
- [Testing Guide](testing.md) - Running and writing tests

---

## What is openLCA IPC?

OpenLCA IPC (Inter-Process Communication) allows you to interact programmatically with the openLCA desktop application. This library wraps the low-level IPC protocol in a high-level, user-friendly Python API.

## Why Use This Library?

### Before (Raw olca-ipc)
```python
# Low-level, verbose code
import olca
client = olca.Client(8080)
response = client.get_descriptors(olca.Flow)
steel_flow = None
for desc in response:
    if 'steel' in desc.name.lower():
        steel_flow = client.get(olca.Flow, desc.id)
        break

# Create exchanges manually
exchange = olca.Exchange()
exchange.flow = steel_flow
exchange.amount = 1.0
# ... many more manual steps
```

### After (This Library)
```python
# High-level, intuitive code
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Simple search
    steel_flow = client.search.find_flow(['steel'])

    # Easy data creation
    process = client.data.create_process(
        name="My Process",
        inputs=[(steel_flow, 1.0)]
    )
```

## Key Features

### 1. Simple, Pythonic API
High-level utilities that abstract complex IPC operations into simple, readable code.

### 2. Comprehensive LCA Workflow
Everything you need for LCA workflows:
- Search and discovery
- Data creation
- Product systems
- Calculations
- Results analysis
- Export utilities

### 3. Advanced Analysis Tools
- **Contribution Analysis** - Identify key contributors to impacts
- **Uncertainty Analysis** - Monte Carlo simulations with statistical summaries
- **Scenario Analysis** - Parameter sensitivity and scenario comparison

### 4. Production-Ready
- Error handling and validation
- Logging and debugging support
- Resource management (automatic cleanup)
- Type hints for IDE support

### 5. AI Agent Friendly
Clear documentation and structured outputs make it ideal for automation and AI agents.

## Module Overview

The library is organized into specialized modules:

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `OLCAClient` | Main client for IPC connection | `test_connection()`, context manager support |
| `search` | Search and discovery | `find_flow()`, `find_process()`, `find_impact_method()` |
| `data` | Create/modify data | `create_product_flow()`, `create_process()`, `create_exchange()` |
| `systems` | Product systems | `create_product_system()`, `auto_complete()` |
| `calculate` | Run calculations | `simple_calculation()`, `contribution_analysis()` |
| `results` | Extract results | `get_total_impacts()`, `get_inventory_results()` |
| `contributions` | Contribution analysis | `get_top_contributors()`, `get_process_contributions()` |
| `uncertainty` | Uncertainty analysis | `run_monte_carlo()`, `compare_with_uncertainty()` |
| `parameters` | Parameter scenarios | `run_scenario_analysis()`, `create_parameter_redef()` |
| `export` | Export utilities | `export_to_csv()`, `export_to_excel()` |

## Quick Example

Here's a complete LCA workflow in just a few lines:

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Search
    steel = client.search.find_flow(['steel'])
    provider = client.search.find_best_provider(steel)

    # Create
    product = client.data.create_product_flow("My Product")
    exchanges = [
        client.data.create_exchange(product, 1.0, is_input=False, is_quantitative_reference=True),
        client.data.create_exchange(steel, 2.5, is_input=True, provider=provider)
    ]
    process = client.data.create_process("My Process", exchanges=exchanges)

    # Calculate
    system = client.systems.create_product_system(process)
    method = client.search.find_impact_method(['TRACI'])
    result = client.calculate.simple_calculation(system, method)

    # Analyze
    impacts = client.results.get_total_impacts(result)
    for impact in impacts:
        print(f"{impact['name']}: {impact['amount']:.4e} {impact['unit']}")

    # Cleanup
    result.dispose()
```

## Documentation Conventions

Throughout this documentation:

- **Code blocks** show runnable examples
- **Important notes** highlight critical information
- **Tips** provide helpful suggestions
- **Warnings** alert you to potential issues

### Code Example Format

```python
# Example code with explanatory comments
client = OLCAClient(port=8080)

# Important: Always dispose results
result = client.calculate.simple_calculation(system, method)
try:
    impacts = client.results.get_total_impacts(result)
finally:
    result.dispose()  # Critical cleanup step
```

## Getting Help

- **Issues**: Report bugs at [GitHub Issues](https://github.com/dernestbank/openlca-ipc/issues)
- **Discussions**: Ask questions at [GitHub Discussions](https://github.com/dernestbank/openlca-ipc/discussions)
- **Email**: dernestbanksch@gmail.com

## License

This project is licensed under the MIT License. See [LICENSE](../LICENSE) for details.

## Acknowledgments

Built on top of:
- [olca-ipc](https://github.com/GreenDelta/olca-ipc.py) by GreenDelta
- [olca-schema](https://github.com/GreenDelta/olca-schema) by GreenDelta
- [openLCA](https://www.openlca.org/) life cycle assessment software

Follows [ISO 14040](https://www.iso.org/standard/37456.html) and [ISO 14044](https://www.iso.org/standard/38498.html) LCA standards.

---

**Next Steps**: Start with the [Installation Guide](installation.md) or jump directly to the [Quick Start Guide](quickstart.md).
