# Best Practices Guide

This guide provides recommended patterns and practices for using the openLCA IPC Python library effectively.

## Code Organization

### Use Context Managers

**Always use `with` statement** for automatic resource cleanup:

```python
# ✓ Good - automatic cleanup
with OLCAClient(port=8080) as client:
    flow = client.search.find_flow(['steel'])
    # Connection automatically closed

# ✗ Avoid - manual cleanup required
client = OLCAClient(port=8080)
flow = client.search.find_flow(['steel'])
client.client.close()  # Easy to forget!
```

### Structure Your Code

Break complex workflows into functions:

```python
from openlca_ipc import OLCAClient

def main():
    """Main LCA workflow."""
    with OLCAClient(port=8080) as client:
        materials = search_materials(client)
        process = create_production_process(client, materials)
        system = build_product_system(client, process)
        impacts = calculate_impacts(client, system)
        analyze_results(impacts)

def search_materials(client):
    """Search for required materials."""
    steel = client.search.find_flow(['steel'])
    aluminum = client.search.find_flow(['aluminum'])

    if not steel or not aluminum:
        raise ValueError("Required materials not found")

    return {
        'steel': steel,
        'aluminum': aluminum
    }

def create_production_process(client, materials):
    """Create the production process."""
    # ... implementation ...
    return process

# etc.
```

### Use Type Hints

Add type hints for better IDE support and documentation:

```python
from typing import List, Optional, Dict
import olca_schema as o
from openlca_ipc import OLCAClient

def find_materials(
    client: OLCAClient,
    material_names: List[str]
) -> Dict[str, o.Ref]:
    """Find multiple materials by name.

    Args:
        client: OLCAClient instance
        material_names: List of material names to search

    Returns:
        Dictionary mapping material names to flow references

    Raises:
        ValueError: If any material not found
    """
    materials = {}
    for name in material_names:
        flow = client.search.find_flow([name])
        if not flow:
            raise ValueError(f"Material not found: {name}")
        materials[name] = flow
    return materials
```

## Error Handling

### Always Check Search Results

```python
# ✓ Good - check before using
steel = client.search.find_flow(['steel'])
if not steel:
    print("Steel not found in database")
    return  # or raise exception

provider = client.search.find_best_provider(steel)
if not provider:
    print("No provider found for steel")
    return

# Now safe to use
exchange = client.data.create_exchange(
    steel, 1.0, is_input=True, provider=provider
)

# ✗ Bad - assumes search succeeds
steel = client.search.find_flow(['steel'])
exchange = client.data.create_exchange(
    steel, 1.0, is_input=True  # Will fail if steel is None!
)
```

### Use Try-Finally for Cleanup

```python
# ✓ Good - ensures disposal even if error occurs
result = client.calculate.simple_calculation(system, method)
try:
    impacts = client.results.get_total_impacts(result)
    # ... process impacts ...
    if some_condition:
        raise ValueError("Something wrong")
finally:
    result.dispose()  # Always executes

# ✗ Bad - disposal skipped if error occurs
result = client.calculate.simple_calculation(system, method)
impacts = client.results.get_total_impacts(result)
# If error above, dispose() never called
result.dispose()
```

### Provide Helpful Error Messages

```python
def find_required_flow(client, keywords: List[str]) -> o.Ref:
    """Find flow or raise helpful error."""
    flow = client.search.find_flow(keywords)

    if not flow:
        # Helpful error message
        keyword_str = ', '.join(keywords)
        raise ValueError(
            f"Flow not found with keywords: {keyword_str}\n"
            f"Suggestions:\n"
            f"1. Check spelling\n"
            f"2. Try broader keywords\n"
            f"3. Verify material exists in database\n"
            f"4. Use find_flows() to see all matches"
        )

    return flow
```

## Resource Management

### Always Dispose Results

```python
# ✓ Good
result = client.calculate.simple_calculation(system, method)
try:
    impacts = client.results.get_total_impacts(result)
    return impacts
finally:
    result.dispose()

# ✗ Bad - memory leak
result = client.calculate.simple_calculation(system, method)
impacts = client.results.get_total_impacts(result)
return impacts  # Result never disposed!
```

### Handle Multiple Results

```python
def run_multiple_calculations(client, systems, method):
    """Calculate impacts for multiple systems."""
    all_impacts = []

    for system in systems:
        result = None
        try:
            result = client.calculate.simple_calculation(system, method)
            impacts = client.results.get_total_impacts(result)
            all_impacts.append({
                'system': system.name,
                'impacts': impacts
            })
        except Exception as e:
            print(f"Calculation failed for {system.name}: {e}")
        finally:
            if result:
                result.dispose()

    return all_impacts
```

### Cache Frequently Used Items

```python
class LCAWorkflow:
    """LCA workflow with cached common items."""

    def __init__(self, client):
        self.client = client

        # Cache impact method
        self._impact_method = None

        # Cache common flows
        self._common_flows = {}

    @property
    def impact_method(self):
        """Get cached impact method."""
        if not self._impact_method:
            self._impact_method = self.client.search.find_impact_method(['TRACI'])
        return self._impact_method

    def get_flow(self, name):
        """Get flow with caching."""
        if name not in self._common_flows:
            flow = self.client.search.find_flow([name])
            if flow:
                self._common_flows[name] = flow
        return self._common_flows.get(name)
```

## Search Strategies

### Use Specific Keywords

```python
# ✓ Good - specific
pet = client.search.find_flow(['polyethylene', 'terephthalate'])

# ✗ Too broad - may get wrong material
plastic = client.search.find_flow(['plastic'])
```

### Handle Search Variants

```python
def find_flow_with_variants(client, variants: List[List[str]]) -> Optional[o.Ref]:
    """Try multiple keyword combinations."""
    for keywords in variants:
        flow = client.search.find_flow(keywords)
        if flow:
            return flow
    return None

# Usage
aluminum = find_flow_with_variants(client, [
    ['aluminum', 'primary'],
    ['aluminium', 'primary'],
    ['Al'],
])
```

### Validate Search Results

```python
def find_product_flow(client, keywords: List[str]) -> o.Ref:
    """Find flow and verify it's a product."""
    flow_ref = client.search.find_flow(keywords)

    if not flow_ref:
        raise ValueError(f"Flow not found: {keywords}")

    # Get full flow to check type
    flow = client.client.get(o.Flow, flow_ref.id)

    if flow.flow_type != o.FlowType.PRODUCT_FLOW:
        raise ValueError(
            f"Found flow '{flow.name}' is {flow.flow_type}, "
            f"expected PRODUCT_FLOW"
        )

    return flow_ref
```

## Data Creation

### Validate Before Creating

```python
def create_process_safe(client, name, inputs, outputs):
    """Create process with validation."""
    # Validate inputs
    if not outputs:
        raise ValueError("Process must have at least one output")

    qref_count = sum(1 for ex in outputs if ex.quantitative_reference)
    if qref_count != 1:
        raise ValueError("Process must have exactly one quantitative reference")

    # Create exchanges
    all_exchanges = inputs + outputs

    # Create process
    process = client.data.create_process(
        name=name,
        exchanges=all_exchanges
    )

    # Verify creation
    created = client.client.get(o.Process, process.id)
    if not created.quantitative_reference:
        raise ValueError("Process created without quantitative reference!")

    return process
```

### Use Descriptive Names

```python
# ✓ Good - descriptive names
widget_production = client.data.create_process(
    name="Widget Assembly - Steel and Aluminum",
    description="Assembles 1 widget from 2kg steel and 1kg aluminum"
)

# ✗ Bad - vague names
process1 = client.data.create_process(name="Process 1")
```

### Document Units and Amounts

```python
# ✓ Good - clear units in description
steel_plate = client.data.create_product_flow(
    name="Steel Plate",
    description="Hot rolled steel plate, 1mm thickness, 1kg"
)

exchange = client.data.create_exchange(
    steel_plate,
    amount=2.5,  # kg, explicitly documented
    is_input=True
)
```

## Calculations

### Show Progress for Long Operations

```python
def run_monte_carlo_with_progress(client, system, method, iterations):
    """Run Monte Carlo with progress reporting."""
    def progress_callback(current, total):
        percent = (current / total) * 100
        print(f"\rProgress: {current}/{total} ({percent:.1f}%)", end='')

    results = client.uncertainty.run_monte_carlo(
        system=system,
        impact_method=method,
        iterations=iterations,
        progress_callback=progress_callback
    )

    print("\n✓ Complete!")
    return results
```

### Validate Calculation Results

```python
def calculate_with_validation(client, system, method):
    """Calculate and validate results."""
    result = client.calculate.simple_calculation(system, method)

    try:
        impacts = client.results.get_total_impacts(result)

        # Validate results
        if not impacts:
            raise ValueError("Calculation returned no impacts")

        # Check for all-zero results
        total_impact = sum(abs(imp['amount']) for imp in impacts)
        if total_impact == 0:
            raise ValueError(
                "All impact values are zero - check:\n"
                "1. Product system has providers\n"
                "2. Impact method is appropriate\n"
                "3. Database has characterization factors"
            )

        return impacts

    finally:
        result.dispose()
```

### Handle Calculation Errors

```python
def calculate_robust(client, system, method, retries=3):
    """Calculate with retry logic."""
    for attempt in range(retries):
        result = None
        try:
            result = client.calculate.simple_calculation(system, method)
            impacts = client.results.get_total_impacts(result)
            return impacts

        except Exception as e:
            if attempt < retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying...")
                time.sleep(2)
            else:
                print(f"All {retries} attempts failed")
                raise

        finally:
            if result:
                result.dispose()
```

## Logging

### Use Logging Instead of Print

```python
import logging

logger = logging.getLogger(__name__)

def process_workflow(client):
    """Run workflow with proper logging."""
    logger.info("Starting LCA workflow")

    steel = client.search.find_flow(['steel'])
    if not steel:
        logger.error("Steel not found in database")
        return

    logger.info(f"Found steel: {steel.name}")

    # ... rest of workflow ...

    logger.info("Workflow completed successfully")
```

### Configure Logging Levels

```python
import logging

# Development - see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Production - errors and warnings only
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Testing

### Write Tests

```python
import pytest
from openlca_ipc import OLCAClient

@pytest.fixture
def client():
    """Provide OLCAClient for tests."""
    return OLCAClient(port=8080)

def test_find_steel(client):
    """Test finding steel flow."""
    steel = client.search.find_flow(['steel'])
    assert steel is not None, "Steel should be in database"
    assert 'steel' in steel.name.lower()

def test_create_process(client):
    """Test process creation."""
    product = client.data.create_product_flow("Test Product")

    exchange = client.data.create_exchange(
        product, 1.0, is_input=False, is_quantitative_reference=True
    )

    process = client.data.create_process(
        "Test Process",
        exchanges=[exchange]
    )

    assert process.id is not None
    assert process.name == "Test Process"
```

### Use Mock for Unit Tests

```python
from unittest.mock import Mock, patch

def test_search_error_handling():
    """Test error handling in search."""
    mock_client = Mock()
    mock_client.search.find_flow.return_value = None

    # Test code that handles None result
    result = mock_client.search.find_flow(['steel'])
    assert result is None
```

## Performance

### Limit Search Results

```python
# ✓ Good - limit results for faster search
flows = client.search.find_flows(['steel'], max_results=5)

# ✗ Slower - searches entire database
flows = client.search.find_flows(['steel'], max_results=1000)
```

### Use Specific Flow Types

```python
# ✓ Good - faster, more specific
products = client.search.find_flows(
    ['steel'],
    flow_type=o.FlowType.PRODUCT_FLOW,
    max_results=10
)

# ✗ Slower - searches all types
all_flows = client.search.find_flows(['steel'], max_results=10)
```

### Batch Operations

```python
# ✓ Good - batch operations
materials = ['steel', 'aluminum', 'copper']
flows = {}

for material in materials:
    flow = client.search.find_flow([material])
    if flow:
        flows[material] = flow

# Process all at once
for name, flow in flows.items():
    # ... create exchanges ...
```

## Documentation

### Document Your Code

```python
def calculate_product_impacts(
    client: OLCAClient,
    product_name: str,
    material_inputs: Dict[str, float],
    impact_method_keywords: List[str]
) -> Dict[str, float]:
    """
    Calculate environmental impacts for a product.

    This function creates a simple process from material inputs,
    builds a product system, and calculates impacts.

    Args:
        client: Connected OLCAClient instance
        product_name: Name of the product to create
        material_inputs: Dict mapping material names to amounts in kg
        impact_method_keywords: Keywords to find impact method

    Returns:
        Dictionary mapping impact category names to values

    Raises:
        ValueError: If required materials not found
        ValueError: If impact method not found

    Example:
        >>> with OLCAClient() as client:
        ...     impacts = calculate_product_impacts(
        ...         client,
        ...         "Widget",
        ...         {'steel': 2.0, 'aluminum': 1.0},
        ...         ['TRACI']
        ...     )
    """
    # Implementation...
```

### Add Comments for Complex Logic

```python
# Check if flow is elementary (no provider needed)
full_flow = client.client.get(o.Flow, flow_ref.id)
if full_flow.flow_type == o.FlowType.ELEMENTARY_FLOW:
    # Elementary flows (CO2, water, etc.) don't have providers
    # They're inputs from or outputs to the environment
    exchange = client.data.create_exchange(
        flow_ref, amount, is_input=True
        # No provider parameter
    )
else:
    # Product/waste flows need providers
    provider = client.search.find_best_provider(flow_ref)
    exchange = client.data.create_exchange(
        flow_ref, amount, is_input=True, provider=provider
    )
```

## Configuration

### Use Configuration Files

```python
# config.py
class Config:
    """LCA workflow configuration."""
    IPC_PORT = 8080
    IMPACT_METHOD = ['TRACI', '2.1']
    DEFAULT_DATABASE = 'USLCI'

# workflow.py
from config import Config

with OLCAClient(port=Config.IPC_PORT) as client:
    method = client.search.find_impact_method(Config.IMPACT_METHOD)
```

### Use Environment Variables

```python
import os
from openlca_ipc import OLCAClient

# Get port from environment, default to 8080
port = int(os.getenv('OPENLCA_PORT', '8080'))

with OLCAClient(port=port) as client:
    # ... workflow ...
```

## Summary Checklist

- [ ] Use `with` statement for OLCAClient
- [ ] Always check search results before using
- [ ] Always dispose calculation results
- [ ] Use try-finally for resource cleanup
- [ ] Provide helpful error messages
- [ ] Cache frequently used items
- [ ] Validate data before creating
- [ ] Use descriptive names
- [ ] Log instead of print
- [ ] Write tests
- [ ] Document your code
- [ ] Handle errors gracefully

## See Also

- [API Reference](api/README.md) - Detailed API documentation
- [Examples](../examples/) - Working code examples
- [Troubleshooting](../documentation/troubleshooting.md) - Common problems and solutions
- [FAQ](../documentation/faq.md) - Frequently asked questions
