# Installation and Setup Guide

This guide will help you install the openLCA IPC Python library and set up your environment.

## Prerequisites

Before installing the library, ensure you have:

### 1. Python 3.10 or Higher

Check your Python version:

```bash
python --version
# or
python3 --version
```

If you need to install or upgrade Python:
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: Use Homebrew: `brew install python@3.11`
- **Linux**: `sudo apt install python3.11` (Ubuntu/Debian) or use your package manager

### 2. openLCA Desktop Application (Version 2.x)

Download and install openLCA from [openlca.org](https://www.openlca.org/download/):

1. Download the appropriate version for your operating system
2. Install following the platform-specific instructions
3. Launch openLCA to verify installation

### 3. A Database

You'll need a database in openLCA:
- Download from [Nexus](https://nexus.openlca.org/databases)
- Or create a new empty database
- Import your own data

## Installation Methods

### Method 1: Install from PyPI (Coming Soon)

Once published to PyPI, you'll be able to install with:

```bash
pip install openlca-ipc
```

### Method 2: Install from Source (Current Method)

#### Clone the Repository

```bash
# Using HTTPS
git clone https://github.com/dernestbank/openlca-ipc.git
cd openlca-ipc

# Or using SSH
git clone git@github.com:dernestbank/openlca-ipc.git
cd openlca-ipc
```

#### Install in Editable Mode

```bash
# Basic installation
pip install -e .

# With optional dependencies (recommended)
pip install -e ".[full]"
```

#### What Gets Installed

**Core Dependencies:**
- `olca-ipc>=2.4.0` - openLCA IPC protocol implementation
- `olca-schema>=2.4.0` - openLCA data schema
- `numpy>=1.24.0` - Numerical operations

**Optional Dependencies** (with `[full]`):
- `scipy>=1.10.0` - Statistical analysis for uncertainty
- `matplotlib>=3.7.0` - Visualization
- `pandas>=2.0.0` - Data export and analysis

### Method 3: Manual Installation

If you prefer manual installation:

```bash
# Clone repository
git clone https://github.com/dernestbank/openlca-ipc.git
cd openlca-ipc

# Install dependencies
pip install -r requirements.txt

# Optionally install dev dependencies
pip install -r requirements-dev.txt
```

## Setting Up openLCA IPC Server

After installation, you need to start the IPC server in openLCA:

### Step 1: Open openLCA

Launch the openLCA desktop application.

### Step 2: Open a Database

1. Click **File → Open Database**
2. Select your database
3. Wait for it to load

### Step 3: Start IPC Server

1. Go to **Tools → Developer Tools → IPC Server**
2. The IPC Server window will open
3. Click **Start** button
4. Note the port number (default: 8080)

![IPC Server Window](images/ipc-server.png)

**Important Notes:**
- Keep openLCA running while using the library
- Keep the IPC server started
- Default port is 8080 (you can change it if needed)

## Verifying Installation

### Test 1: Import the Library

```python
# test_import.py
try:
    from openlca_ipc import OLCAClient
    print("✓ Library imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
```

Run:
```bash
python test_import.py
```

### Test 2: Connect to openLCA

```python
# test_connection.py
from openlca_ipc import OLCAClient

try:
    client = OLCAClient(port=8080)
    print("✓ Connected to openLCA")

    if client.test_connection():
        print("✓ Connection test passed")
    else:
        print("✗ Connection test failed")
except ConnectionError as e:
    print(f"✗ Connection failed: {e}")
    print("\nMake sure:")
    print("1. openLCA is running")
    print("2. A database is open")
    print("3. IPC server is started")
```

Run:
```bash
python test_connection.py
```

Expected output:
```
✓ Connected to openLCA
✓ Connection test passed
```

### Test 3: Basic Operations

```python
# test_operations.py
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    # Test search
    flows = client.search.find_flows(['steel'], max_results=5)
    print(f"✓ Found {len(flows)} steel-related flows")

    # Test finding impact method
    method = client.search.find_impact_method(['TRACI'])
    if method:
        print(f"✓ Found impact method: {method.name}")
    else:
        print("✗ No impact method found (database may not have methods)")

print("✓ All operations completed successfully")
```

## Development Setup

If you plan to contribute or modify the library:

### 1. Clone and Install in Development Mode

```bash
git clone https://github.com/dernestbank/openlca-ipc.git
cd openlca-ipc

# Install with all dependencies including dev tools
pip install -e ".[full]"
pip install -r requirements-dev.txt
```

### 2. Verify Development Tools

```bash
# Code formatting
black --version

# Linting
flake8 --version

# Type checking
mypy --version

# Testing
pytest --version
```

### 3. Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=openlca_ipc tests/

# Run specific test file
pytest tests/test_search.py
```

### 4. Code Quality Checks

```bash
# Format code
black openlca_ipc/

# Check style
flake8 openlca_ipc/

# Type checking
mypy openlca_ipc/
```

## Environment Setup

### Using Virtual Environments (Recommended)

#### venv (Built-in)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install library
pip install -e ".[full]"
```

#### Conda

```bash
# Create environment
conda create -n openlca_env python=3.11

# Activate
conda activate openlca_env

# Install library
pip install -e ".[full]"
```

### IDE Setup

#### VS Code

Install recommended extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer

Create `.vscode/settings.json`:
```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

#### PyCharm

1. Open the project folder
2. Configure Python interpreter (Settings → Project → Python Interpreter)
3. Enable pytest (Settings → Tools → Python Integrated Tools → Testing)

## Troubleshooting Installation

### Issue: Module Not Found After Installation

**Problem:**
```python
ImportError: No module named 'openlca_ipc'
```

**Solutions:**
1. Verify installation: `pip list | grep openlca`
2. Check you're using the correct Python/pip
3. Reinstall: `pip install -e . --force-reinstall`

### Issue: olca-ipc Version Conflicts

**Problem:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed...
```

**Solution:**
```bash
# Uninstall conflicting versions
pip uninstall olca-ipc olca-schema

# Reinstall with specific versions
pip install olca-ipc==2.4.0 olca-schema==2.4.0

# Then install this library
pip install -e .
```

### Issue: Cannot Connect to IPC Server

**Problem:**
```python
ConnectionError: Could not connect to openLCA IPC server on port 8080
```

**Solutions:**
1. **Check openLCA is running**
   - Launch the openLCA desktop application

2. **Check database is open**
   - File → Open Database in openLCA

3. **Start IPC server**
   - Tools → Developer Tools → IPC Server
   - Click "Start"

4. **Verify port number**
   - Check port in IPC server window
   - Use same port in Python:
     ```python
     client = OLCAClient(port=8080)  # Match the port
     ```

5. **Check firewall**
   - Ensure localhost connections allowed
   - Try disabling firewall temporarily

6. **Restart openLCA**
   - Close openLCA completely
   - Reopen and restart IPC server

### Issue: Import Errors for Optional Dependencies

**Problem:**
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

## Platform-Specific Notes

### Windows

- Use Command Prompt or PowerShell
- May need to use `py` instead of `python`:
  ```bash
  py -m pip install -e ".[full]"
  ```

### macOS

- May need to use `python3` and `pip3`:
  ```bash
  python3 -m pip install -e ".[full]"
  ```
- On M1/M2 Macs, ensure you're using ARM-compatible Python

### Linux

- May need to install Python dev headers:
  ```bash
  sudo apt install python3-dev  # Ubuntu/Debian
  sudo yum install python3-devel  # CentOS/RHEL
  ```

## Next Steps

After successful installation:

1. **[Quick Start Guide](quickstart.md)** - Get started with basic usage
2. **[Tutorials](tutorials/README.md)** - Step-by-step guides
3. **[API Reference](api/README.md)** - Detailed API documentation
4. **[Examples](../examples/README.md)** - Working code examples

## Getting Help

If you encounter issues not covered here:

- **GitHub Issues**: [Report a bug](https://github.com/dernestbank/openlca-ipc/issues)
- **Discussions**: [Ask a question](https://github.com/dernestbank/openlca-ipc/discussions)
- **Email**: dernestbanksch@gmail.com
