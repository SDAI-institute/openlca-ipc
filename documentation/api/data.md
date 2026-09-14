# DataBuilder API

`DataBuilder` creates foreground flows, exchanges, and unit processes through the active openLCA IPC connection.

## Access

```python
from openlca_ipc import OLCAClient

with OLCAClient(port=8080) as client:
    data = client.data
```

## `create_product_flow(name, description="")`

Creates a product flow using the database Mass flow property as its reference property.

## `create_exchange(flow, amount, is_input, is_quantitative_reference=False, provider=None, *, unit=None, flow_property=None, formula=None)`

Builds an exchange object for later insertion into a process. By default, v0.4.1 derives the exchange property and unit from the flow's own reference flow property. This is important for non-mass flows such as energy or goods transport.

Use `unit` and `flow_property` only when intentionally recording the amount in another property defined by that flow. `formula` can retain an openLCA amount formula such as `"0.065*500"`.

## `create_process(name, description="", exchanges=None)`

Creates a unit process and writes it to the active database. A valid foreground process should normally contain exactly one quantitative-reference exchange.

## `check_mass_balance(process, *, rel_tol=1e-3)`

Checks Mass-property inputs and outputs after converting them to kg. It returns warning strings rather than raising. Non-mass properties are intentionally excluded because their units are not dimensionally comparable.

## Example

```python
product = client.data.create_product_flow("Widget")
steel = client.search.find_flow(["steel"])
provider = client.search.find_best_provider(steel)

exchanges = [
    client.data.create_exchange(product, 1, False, True),
    client.data.create_exchange(steel, 2, True, provider=provider),
]
process = client.data.create_process("Widget production", exchanges=exchanges)

for warning in client.data.check_mass_balance(process):
    print(warning)
```

## Review points

- Writes affect the active openLCA database.
- In `OLCAClient(read_only=True)`, database writes are blocked before reaching openLCA.
- Confirm units and provider linking before interpreting results.
- A balanced mass inventory does not by itself establish a valid LCA model.
