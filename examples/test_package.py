

#%%
from openlca_ipc import OLCAClient

# Initialize
with OLCAClient(port=8080) as client:
    # Search
    steel = client.search.find_flow(['steel'])
    provider = client.search.find_best_provider(steel)
    
    # Create process
    product = client.data.create_product_flow("Steel plate")
    exchanges = [
        client.data.create_exchange(product, 1.0, False, True),
        client.data.create_exchange(steel, 1.0, True, provider=provider)
    ]
    process = client.data.create_process("Plate production", exchanges=exchanges)
    
    # Calculate
    system = client.systems.create_product_system(process)
    method = client.search.find_impact_method(['TRACI'])
    result = client.calculate.simple_calculation(system, method)
    
    # Results
    impacts = client.results.get_total_impacts(result)
    for impact in impacts:
        print(f"{impact['name']}: {impact['amount']:.4e}")
    
result.dispose()



#%%

#Example 2: Contribution Analysis

from openlca_ipc import OLCAClient

client = OLCAClient(port=8080)

# Calculate with contributions
result = client.calculate.contribution_analysis(system, method)

# Get all impacts
impacts = client.results.get_total_impacts(result)

# Analyze each impact
for impact in impacts:
    print(f"\n{impact['name']}:")
    
    # Top 5 contributors
    contribs = client.contributions.get_top_contributors(
        result, impact['category'], n=5
    )
    
    for i, c in enumerate(contribs, 1):
        print(f"  {i}. {c.name}: {c.share*100:.1f}%")

result.dispose()


#%%

# Example 3: Monte Carlo with Plotting

from openlca_ipc import OLCAClient
import matplotlib.pyplot as plt
import numpy as np

client = OLCAClient(port=8080)

# Run uncertainty analysis
results = client.uncertainty.run_monte_carlo(
    system=my_system,
    impact_method=traci,
    iterations=1000
)

# Plot distribution for global warming
gwp_name = next(k for k in results.keys() if 'warming' in k.lower())
gwp_data = results[gwp_name]

plt.figure(figsize=(10, 6))
plt.hist(gwp_data.values, bins=50, edgecolor='black', alpha=0.7)
plt.axvline(gwp_data.mean, color='red', linestyle='--', label='Mean')
plt.axvline(gwp_data.percentile_5, color='orange', linestyle=':', label='5th %ile')
plt.axvline(gwp_data.percentile_95, color='orange', linestyle=':', label='95th %ile')
plt.xlabel('Global Warming Potential')
plt.ylabel('Frequency')
plt.title('Global Warming - Monte Carlo Distribution')
plt.legend()
plt.savefig('gwp_distribution.png')
print("Plot saved to gwp_distribution.png")





#%%





#%%


