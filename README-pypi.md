# openLCA IPC Python Library

A comprehensive Python library for interacting with openLCA desktop application through the IPC (Inter-Process Communication) protocol. Built for life cycle assessment (LCA) workflows based on ISO-14040/14044 standards.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![openLCA](https://img.shields.io/badge/openLCA-2.x-orange.svg)](https://www.openlca.org/)
[![DOI](https://zenodo.org/badge/1082686834.svg)](https://doi.org/10.5281/zenodo.17567634)

You can cite all versions by using the DOI 10.5281/zenodo.17567634. This DOI represents all versions, and will always resolve to the latest one.

## Features

- **Simple, Pythonic API** - High-level utilities that abstract complex IPC operations
- **Comprehensive LCA Workflow** - Search, create, calculate, and analyze in one package
- **Contribution Analysis** - Identify key contributors to environmental impacts
- **Uncertainty Analysis** - Monte Carlo simulations with statistical summaries
- **Scenario Analysis** - Parameter sensitivity and scenario comparison
- **Export Utilities** - CSV and Excel export for results
- **AI Agent Friendly** - Clear documentation and structured outputs for automation
- **MCP Server** - Model Context Protocol server for n8n and AI workflow automation
- **ISO Compliant** - Follows ISO-14040/14044 LCA standards

## Installation

### Prerequisites

- Python 3.10 or higher
- openLCA desktop application (version 2.x)
- openLCA IPC server running (Tools → Developer Tools → IPC Server)

### Install from PyPI (Coming Soon)

```bash
pip install openlca-ipc
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/dernestbank/openlca-ipc.git
cd openlca-ipc

# Install in editable mode
pip install -e .

# Or install with optional dependencies
pip install -e ".[full]"
```

### Install Dependencies

```bash
# Core dependencies only
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

## Quick Start

### 1. Start openLCA IPC Server

Before using the library, start the IPC server in openLCA:

1. Open openLCA desktop application
2. Go to **Tools → Developer Tools → IPC Server**
3. Click **Start** (default port: 8080)

### 2. Basic Usage

```python
from openlca_ipc import OLCAClient

# Connect to openLCA
with OLCAClient(port=8080) as client:
    # Test connection
    if client.test_connection():
        print("Connected to openLCA!")

    # Search for a material
    steel_flow = client.search.find_flow(['steel', 'production'])
    print(f"Found: {steel_flow.name}")

    # Find provider process
    provider = client.search.find_best_provider(steel_flow)
    print(f"Provider: {provider.name if provider else 'None'}")
```

## Usage Examples

### Example 1: Complete LCA Workflow

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # 1. Search for materials
    steel = client.search.find_flow(['steel'])
    steel_provider = client.search.find_best_provider(steel)

    # 2. Create a new process
    product = client.data.create_product_flow("Steel plate")
    exchanges = [
        client.data.create_exchange(product, 1.0, is_input=False, is_quantitative_reference=True),
        client.data.create_exchange(steel, 1.0, is_input=True, provider=steel_provider)
    ]
    process = client.data.create_process("Plate production", exchanges=exchanges)

    # 3. Create product system
    system = client.systems.create_product_system(process)

    # 4. Select impact method
    method = client.search.find_impact_method(['TRACI'])

    # 5. Calculate impacts
    result = client.calculate.simple_calculation(system, method)

    # 6. Get results
    impacts = client.results.get_total_impacts(result)
    for impact in impacts:
        print(f"{impact['name']}: {impact['amount']:.4e} {impact['unit']}")

    # 7. Clean up
    result.dispose()
```

### Example 2: Contribution Analysis

```python
from openlca_ipc import OLCAClient

client = OLCAClient(port=8080)

# Run calculation with contribution analysis
result = client.calculate.contribution_analysis(system, method)

# Get all impacts
impacts = client.results.get_total_impacts(result)

# Analyze top contributors for each impact
for impact in impacts:
    print(f"\n{impact['name']}:")

    # Get top 5 contributors
    contributors = client.contributions.get_top_contributors(
        result,
        impact['category'],
        n=5,
        min_share=0.01  # Minimum 1% contribution
    )

    for i, contrib in enumerate(contributors, 1):
        print(f"  {i}. {contrib.name}: {contrib.share*100:.1f}% ({contrib.amount:.4e})")

result.dispose()
```

### Example 3: Monte Carlo Uncertainty Analysis

```python
from openlca_ipc import OLCAClient
import matplotlib.pyplot as plt

client = OLCAClient(port=8080)

# Run Monte Carlo simulation
results = client.uncertainty.run_monte_carlo(
    system=my_system,
    impact_method=traci_method,
    iterations=1000,
    progress_callback=lambda i, total: print(f"Progress: {i}/{total}")
)

# Analyze global warming potential
gwp_key = next(k for k in results.keys() if 'warming' in k.lower())
gwp_result = results[gwp_key]

print(f"Mean: {gwp_result.mean:.4e}")
print(f"Std Dev: {gwp_result.std:.4e}")
print(f"CV: {gwp_result.cv:.2%}")
print(f"95% CI: [{gwp_result.percentile_5:.4e}, {gwp_result.percentile_95:.4e}]")

# Plot distribution
plt.figure(figsize=(10, 6))
plt.hist(gwp_result.values, bins=50, edgecolor='black', alpha=0.7)
plt.axvline(gwp_result.mean, color='red', linestyle='--', label='Mean')
plt.xlabel('Global Warming Potential')
plt.ylabel('Frequency')
plt.title('Monte Carlo Simulation Results')
plt.legend()
plt.savefig('gwp_distribution.png')
```

### Example 4: Scenario Analysis

```python
from openlca_ipc import OLCAClient
import pandas as pd

client = OLCAClient(port=8080)

# Analyze how transport distance affects impacts
scenarios = client.parameters.run_scenario_analysis(
    system=transport_system,
    impact_method=traci_method,
    parameter_name='transport_distance',
    values=[100, 200, 500, 1000, 2000, 5000]
)

# Create comparison DataFrame
data = []
for distance, impacts in scenarios.items():
    row = {'Distance (km)': distance}
    for impact in impacts:
        row[impact['name']] = impact['amount']
    data.append(row)

df = pd.DataFrame(data)
print(df)

# Export to CSV
client.export.export_comparison_to_csv(scenarios, 'scenario_results.csv')
```


## Module Overview

The library is organized into specialized modules:

- **`OLCAClient`** - Main client for connecting to openLCA IPC server
- **`search`** - Search and discovery utilities for flows, processes, and impact methods
- **`data`** - Create and modify flows, exchanges, and processes
- **`systems`** - Build and configure product systems
- **`calculate`** - Run LCA calculations with various configurations
- **`results`** - Extract and format calculation results
- **`contributions`** - Analyze contributions by process or flow
- **`uncertainty`** - Monte Carlo simulations and statistical analysis
- **`parameters`** - Parameter scenarios and sensitivity analysis
- **`export`** - Export results to CSV, Excel, and other formats

## Best Practices

### 1. Always Dispose Results

```python
# Good - automatic cleanup with context manager
with OLCAClient(port=8080) as client:
    result = client.calculate.simple_calculation(system, method)
    impacts = client.results.get_total_impacts(result)
    result.dispose()  # Always dispose!

# Also good - explicit cleanup
client = OLCAClient(port=8080)
try:
    result = client.calculate.simple_calculation(system, method)
    # Process results
finally:
    result.dispose()
```

### 2. Handle Missing Data

```python
# Always check search results
pet_flow = client.search.find_flow(['polyethylene', 'terephthalate'])

if not pet_flow:
    # Try alternative keywords
    pet_flow = client.search.find_flow(['PET'])

if not pet_flow:
    print("Material not found in database")
    return

# Proceed safely
provider = client.search.find_best_provider(pet_flow)
```

### 3. Use Logging

```python
import logging

# Enable logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Library modules will log automatically
client = OLCAClient(port=8080)
# Output: "INFO - Connected to openLCA IPC server on port 8080"
```

## Documentation

- **[Setup Guide](https://github.com/dernestbank/openlca-ipc/blob/main/documentation/installation.md)** - Detailed installation and configuration
- **[Examples](https://github.com/dernestbank/openlca-ipc/tree/main/examples)** - Working example scripts and Jupyter notebooks
- **[Complete Documentation](https://github.com/dernestbank/openlca-ipc/blob/main/documentation/index.md)** - Full documentation hub
- **[Quick start guide](https://github.com/dernestbank/openlca-ipc/blob/main/documentation/quickstart.md)** - Module structure and API details
- **[MCP Server](https://github.com/dernestbank/openlca-mcp)** - For AI agent automation (standalone repo)

## Requirements

### Core Dependencies

- `olca-ipc>=2.4.0` - openLCA IPC protocol implementation
- `olca-schema>=2.4.0` - openLCA data schema
- `numpy>=1.24.0` - Numerical operations

### Optional Dependencies

Install with `pip install openlca-ipc[full]`:

- `scipy>=1.10.0` - Statistical analysis for uncertainty
- `matplotlib>=3.7.0` - Visualization
- `pandas>=2.0.0` - Data export and analysis

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/dernestbank/openlca-ipc.git
cd openlca-ipc

# Create conda environment (if using conda)
conda create -n openlca_dev python=3.11
conda activate openlca_dev

# Install in editable mode with dev dependencies
pip install -e ".[full]"
pip install -r requirements-dev.txt
```


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Connection Refused Error

**Problem**: Cannot connect to openLCA IPC server

**Solution**:
1. Ensure openLCA desktop application is running
2. Start IPC server: Tools → Developer Tools → IPC Server
3. Check port number (default: 8080)
4. Verify firewall settings

### Material Not Found

**Problem**: Search returns `None` for materials

**Solution**:
1. Check if the material exists in your openLCA database
2. Try different search keywords
3. Use partial matching: `client.search.find_flows(['steel'])` instead of exact names

### Zero Impact Values

**Problem**: All impact values are zero or very small

**Solution**:
1. Verify that input exchanges have providers linked
2. Check that the product system was created correctly
3. Ensure the impact method is appropriate for your flows
4. Verify that your database has characterization factors

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Citation

If you use this library in your research, please cite:

```bibtex
@software{openlca_ipc,
  author = {Danquah Boakye, Ernest},
  title = {openLCA IPC Python Library},
  year = {2025},
  url = {https://github.com/dernestbank/openlca-ipc}
}
```

## Acknowledgments

- Built on top of [olca-ipc](https://github.com/GreenDelta/olca-ipc.py) and [olca-schema](https://github.com/GreenDelta/olca-schema)
- Follows [ISO 14040](https://www.iso.org/standard/37456.html) and [ISO 14044](https://www.iso.org/standard/38498.html) standards
- Inspired by the openLCA community and LCA practitioners worldwide

## Support

- **Issues**: [GitHub Issues](https://github.com/dernestbank/openlca-ipc/issues)
- **Documentation**: [Read the Docs](https://github.com/dernestbank/openlca-ipc/blob/main/documentation/DOCUMENTATION_MAP.md)
- **Email**: dernestbanksch@gmail.com

---

**Made with ❤️ for the LCA Community**


