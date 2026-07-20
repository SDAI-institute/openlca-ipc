# Documentation Map

Complete guide to all available documentation for the openLCA IPC Python library.

## Quick Navigation

### For New Users
1. [Installation Guide](../documentation/installation.md) - Install and set up
2. [Quick Start Guide](quickstart.md) - Get running in 5 minutes
3. [Examples](../examples/README.md) - Working code examples

### For Regular Users
- [API Reference](api/README.md) - Complete API documentation
- [Best Practices](../documentation/best-practices.md) - Recommended patterns
- [FAQ](../documentation/faq.md) - Common questions

### For Troubleshooting
- [Troubleshooting Guide](../documentation/troubleshooting.md) - Solve common problems
- [FAQ](../documentation/faq.md) - Frequently asked questions

## Complete Documentation Structure

```
docs/
├── index.md                      # Main documentation hub
├── installation.md               # Installation and setup
├── quickstart.md                # 5-minute quick start
├── faq.md                       # Frequently asked questions
├── troubleshooting.md           # Common problems and solutions
├── best-practices.md            # Recommended patterns
├── DOCUMENTATION_MAP.md         # This file
│
├── api/                         # API Reference
│   ├── README.md               # API overview
│   ├── client.md               # OLCAClient documentation
│   ├── search.md               # SearchUtils documentation
│   └── [other modules]         # Additional module docs
│
└── tutorials/                   # (Future) Step-by-step tutorials
    └── README.md
```

## Documentation by Topic

### Getting Started

| Document | Purpose | Time |
|----------|---------|------|
| [Installation Guide](../documentation/installation.md) | Install library and setup environment | 10 min |
| [Quick Start](quickstart.md) | Basic usage tutorial | 5 min |
| [Examples Overview](../examples/README.md) | Overview of example scripts | 5 min |

### Using the Library

| Topic | Document | Description |
|-------|----------|-------------|
| **Core API** | [API Reference](api/README.md) | Complete API documentation |
| **Client** | [OLCAClient](api/client.md) | Connection and setup |
| **Search** | [SearchUtils](api/search.md) | Finding flows and processes |
| **Data** | [DataBuilder](api/README.md) | Creating data |
| **Systems** | [SystemBuilder](api/README.md) | Product systems |
| **Calculations** | [CalculationManager](api/README.md) | Running calculations |
| **Results** | [ResultsAnalyzer](api/README.md) | Extracting results |

### Problem Solving

| Problem Type | Document | Description |
|--------------|----------|-------------|
| **Can't connect** | [Troubleshooting](../documentation/troubleshooting.md#connection-problems) | Connection issues |
| **Can't find data** | [Troubleshooting](../documentation/troubleshooting.md#search-problems) | Search problems |
| **Zero impacts** | [Troubleshooting](../documentation/troubleshooting.md#calculation-problems) | Calculation issues |
| **General questions** | [FAQ](../documentation/faq.md) | Common questions |

### Best Practices

| Topic | Document | Description |
|-------|----------|-------------|
| **Code organization** | [Best Practices](../documentation/best-practices.md#code-organization) | Structure your code |
| **Error handling** | [Best Practices](../documentation/best-practices.md#error-handling) | Handle errors properly |
| **Resource management** | [Best Practices](../documentation/best-practices.md#resource-management) | Cleanup and disposal |
| **Search strategies** | [Best Practices](../documentation/best-practices.md#search-strategies) | Effective searching |
| **Performance** | [Best Practices](../documentation/best-practices.md#performance) | Optimize your code |

## Documentation by User Type

### Beginners

**Start here:**
1. [Installation Guide](../documentation/installation.md) - Set up your environment
2. [Quick Start](quickstart.md) - First program in 5 minutes
3. [FAQ](../documentation/faq.md) - Common questions

**Then:**
- [Examples](../examples/README.md) - Learn from examples
- [API Reference](api/README.md) - Understand the API

### Intermediate Users

**Reference:**
- [API Reference](api/README.md) - Detailed API docs
- [Best Practices](../documentation/best-practices.md) - Recommended patterns

**Troubleshooting:**
- [Troubleshooting Guide](../documentation/troubleshooting.md) - Solve problems
- [FAQ](../documentation/faq.md) - Quick answers

### Advanced Users

**Deep dive:**
- [Advanced Usage](advanced-usage.md) - Advanced patterns
- [API Reference](api/README.md) - Complete API
- [Best Practices](../documentation/best-practices.md) - Expert patterns

### Contributors

**Development:**
- [Installation Guide](../documentation/installation.md#development-setup) - Dev environment
- [Best Practices](../documentation/best-practices.md#testing) - Testing guidelines
- Contributing Guide (coming soon)

## Documentation by Task

### Installation and Setup

1. [Prerequisites](../documentation/installation.md#prerequisites) - What you need
2. [Installation](../documentation/installation.md#installation-methods) - How to install
3. [Starting IPC Server](../documentation/installation.md#setting-up-openlca-ipc-server) - Enable IPC
4. [Verify Installation](../documentation/installation.md#verifying-installation) - Test it works

### First LCA

1. [Quick Start](quickstart.md) - Complete tutorial
2. [Step 1: Connect](quickstart.md#step-2-test-connection) - Test connection
3. [Step 2: Search](quickstart.md#step-3-your-first-search) - Find materials
4. [Step 3: Create](quickstart.md#step-4-create-a-simple-process) - Create process
5. [Step 4: Calculate](quickstart.md#step-5-run-a-calculation) - Run calculation
6. [Step 5: Analyze](quickstart.md#step-6-contribution-analysis) - Analyze results

### Searching for Data

1. [Search Overview](api/search.md) - SearchUtils introduction
2. [Finding Flows](api/search.md#find_flows) - Search for materials
3. [Finding Providers](api/search.md#find_providers) - Find producers
4. [Finding Methods](api/search.md#find_impact_method) - Impact methods
5. [Search Tips](api/search.md#search-tips) - Best practices

### Creating Data

1. [Data Overview](api/README.md) - DataBuilder introduction
2. [Creating Flows](api/README.md) - New materials
3. [Creating Exchanges](api/README.md) - Process inputs/outputs
4. [Creating Processes](api/README.md) - New processes
5. [Best Practices](../documentation/best-practices.md#data-creation) - Recommendations

### Running Calculations

1. [Calculation Overview](api/README.md) - CalculationManager intro
2. [Simple Calculation](api/README.md) - Basic LCA
3. [Contribution Analysis](api/README.md) - Find contributors
4. [Uncertainty Analysis](api/README.md) - Monte Carlo
5. [Best Practices](../documentation/best-practices.md#calculations) - Recommendations

### Solving Problems

1. [Connection Issues](../documentation/troubleshooting.md#connection-problems) - Can't connect
2. [Search Issues](../documentation/troubleshooting.md#search-problems) - Can't find data
3. [Calculation Issues](../documentation/troubleshooting.md#calculation-problems) - Results problems
4. [Memory Issues](../documentation/troubleshooting.md#memory-problems) - Memory leaks
5. [Import Errors](../documentation/troubleshooting.md#import-errors) - Module not found

## Search the Documentation

### By Error Message

| Error | Solution |
|-------|----------|
| `ConnectionError` | [Connection Problems](../documentation/troubleshooting.md#connection-problems) |
| `find_flow() returns None` | [Search Problems](../documentation/troubleshooting.md#search-problems) |
| `All impacts are zero` | [Calculation Problems](../documentation/troubleshooting.md#calculation-problems) |
| `No module named 'openlca_ipc'` | [Import Errors](../documentation/troubleshooting.md#import-errors) |
| `Result has no attribute 'amount'` | [Calculation Problems](../documentation/troubleshooting.md#calculation-problems) |

### By Question

| Question | Answer |
|----------|--------|
| How do I install? | [Installation Guide](../documentation/installation.md) |
| How do I connect? | [Quick Start](quickstart.md#step-2-test-connection) |
| How do I search? | [SearchUtils API](api/search.md) |
| How do I create processes? | [DataBuilder API](api/README.md) |
| How do I calculate? | [Quick Start](quickstart.md#step-5-run-a-calculation) |
| Why are impacts zero? | [Troubleshooting](../documentation/troubleshooting.md#calculation-problems) |
| How do I dispose results? | [Best Practices](../documentation/best-practices.md#resource-management) |

### By Keyword

- **Connection**: [Installation](../documentation/installation.md#setting-up-openlca-ipc-server), [Troubleshooting](../documentation/troubleshooting.md#connection-problems)
- **Search**: [SearchUtils API](api/search.md), [Best Practices](../documentation/best-practices.md#search-strategies)
- **Create**: [DataBuilder API](api/README.md), [Quick Start](quickstart.md#step-4-create-a-simple-process)
- **Calculate**: [Quick Start](quickstart.md#step-5-run-a-calculation), [CalculationManager API](api/README.md)
- **Results**: [ResultsAnalyzer API](api/README.md), [Quick Start](quickstart.md#step-5-run-a-calculation)
- **Error**: [Troubleshooting](../documentation/troubleshooting.md), [FAQ](../documentation/faq.md)
- **Performance**: [Best Practices](../documentation/best-practices.md#performance)
- **Testing**: [Best Practices](../documentation/best-practices.md#testing)

## Documentation Status

### Complete ✓
- [x] Main index
- [x] Installation guide
- [x] Quick start guide
- [x] API reference (core modules)
- [x] FAQ
- [x] Troubleshooting guide
- [x] Best practices
- [x] Examples overview

### In Progress
- [ ] Complete API reference (all modules)
- [ ] Step-by-step tutorials
- [ ] Advanced usage guide
- [ ] Migration guide
- [ ] Contributing guide

### Planned
- [ ] Video tutorials
- [ ] Jupyter notebook examples
- [ ] Case studies
- [ ] Performance benchmarks

## Contributing to Documentation

Found an issue? Want to improve docs?

1. **Report issues**: [GitHub Issues](https://github.com/dernestbank/openlca-ipc/issues)
2. **Suggest improvements**: [Discussions](https://github.com/dernestbank/openlca-ipc/discussions)
3. **Submit changes**: Pull requests welcome!

## Getting Help

Can't find what you need?

1. **Search this map** - Use Ctrl+F to find topics
2. **Check FAQ** - [Frequently Asked Questions](../documentation/faq.md)
3. **Search issues** - [GitHub Issues](https://github.com/dernestbank/openlca-ipc/issues)
4. **Ask question** - [Discussions](https://github.com/dernestbank/openlca-ipc/discussions)
5. **Email** - dernestbanksch@gmail.com

---

**Last Updated**: 2025-01-09

Return to [Documentation Index](../documentation/index.md)
