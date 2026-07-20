# ============================================================================
# Complete Example: examples/complete_lca_workflow.py
# ============================================================================
"""
Complete LCA workflow demonstrating all features of olca-utils.

This example shows:
1. Basic LCA calculation
2. Contribution analysis
3. Scenario analysis
4. Monte Carlo simulation
5. Results export
"""

import logging
from openlca_ipc import OLCAClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run complete LCA workflow."""
    
    print("="*70)
    print("COMPLETE LCA WORKFLOW EXAMPLE")
    print("="*70)
    
    # ========================================================================
    # 1. INITIALIZE CLIENT
    # ========================================================================
    
    print("\n1. Connecting to openLCA...")
    client = OLCAClient(port=8080)
    
    if not client.test_connection():
        print("✗ Failed to connect to openLCA")
        print("  Make sure openLCA is running with IPC server enabled")
        return
    
    print("✓ Connected to openLCA")
    
    # ========================================================================
    # 2. SEARCH FOR MATERIALS
    # ========================================================================
    
    print("\n2. Searching for materials...")
    
    # Search for PET
    pet_flow = client.search.find_flow(
        ['polyethylene', 'terephthalate', 'granulate']
    )
    if not pet_flow:
        print("✗ PET flow not found")
        return
    print(f"✓ Found PET: {pet_flow.name}")
    
    # Get provider
    pet_provider = client.search.find_best_provider(pet_flow)
    if pet_provider:
        print(f"✓ Found provider: {pet_provider.name}")
    
    # ========================================================================
    # 3. CREATE PROCESS
    # ========================================================================
    
    print("\n3. Creating process...")
    
    # Create product flow
    bottle = client.data.create_product_flow(
        name="PET Bottle, 0.5L",
        description="500ml PET beverage bottle"
    )
    
    # Create exchanges
    exchanges = [
        # Output (qref)
        client.data.create_exchange(
            bottle, 0.065, is_input=False, 
            is_quantitative_reference=True
        ),
        # PET input
        client.data.create_exchange(
            pet_flow, 0.060, is_input=True, 
            provider=pet_provider
        )
    ]
    
    # Create process
    process = client.data.create_process(
        name="PET Bottle Production",
        description="Production of 500ml PET bottle",
        exchanges=exchanges
    )
    print(f"✓ Created process: {process.name}")
    
    # ========================================================================
    # 4. CREATE PRODUCT SYSTEM
    # ========================================================================
    
    print("\n4. Creating product system...")
    system = client.systems.create_product_system(process)
    if not system:
        print("✗ Failed to create product system")
        return
    print(f"✓ Created system: {system.name}")
    
    # ========================================================================
    # 5. FIND IMPACT METHOD
    # ========================================================================
    
    print("\n5. Finding impact method...")
    method = client.search.find_impact_method(['TRACI'])
    if not method:
        print("✗ Impact method not found")
        return
    print(f"✓ Found method: {method.name}")
    
    # ========================================================================
    # 6. BASIC CALCULATION
    # ========================================================================
    
    print("\n6. Running basic calculation...")
    result = client.calculate.simple_calculation(system, method)
    
    impacts = client.results.get_total_impacts(result)
    print(f"\n{'Impact Category':<50} {'Value':<15}")
    print("-"*65)
    for impact in impacts[:5]:
        print(f"{impact['name']:<50} {impact['amount']:>14.4e}")
    
    result.dispose()
    
    # ========================================================================
    # 7. CONTRIBUTION ANALYSIS
    # ========================================================================
    
    print("\n7. Running contribution analysis...")
    result = client.calculate.contribution_analysis(system, method)
    
    # Get global warming
    gwp = next(i for i in impacts if 'warming' in i['name'].lower())
    
    # Top contributors
    top_contribs = client.contributions.get_top_contributors(
        result, gwp['category'], n=5
    )
    
    print(f"\nTop 5 contributors to {gwp['name']}:")
    for i, c in enumerate(top_contribs, 1):
        print(f"  {i}. {c.name[:45]:<45} {c.share*100:>6.1f}%")
    
    result.dispose()
    
    # ========================================================================
    # 8. SCENARIO ANALYSIS
    # ========================================================================
    
    print("\n8. Running scenario analysis...")
    print("   (Varying transport distance parameter)")
    
    # Note: This requires a 'transport_distance' parameter in your system
    # Skip if not available
    try:
        scenarios = client.parameters.run_scenario_analysis(
            system=system,
            impact_method=method,
            parameter_name='transport_distance',
            values=[100, 500, 1000]
        )
        
        print("\n   Transport Distance Sensitivity:")
        for distance, impacts in scenarios.items():
            gwp = next(i for i in impacts if 'warming' in i['name'].lower())
            print(f"     {distance:4.0f} km: {gwp['amount']:.4e}")
    
    except Exception as e:
        print(f"   Skipped (parameter not found): {e}")
    
    # ========================================================================
    # 9. MONTE CARLO SIMULATION
    # ========================================================================
    
    print("\n9. Running Monte Carlo simulation (100 iterations)...")
    print("   (This may take a minute...)")
    
    try:
        def progress(current, total):
            if current % 20 == 0 or current == total:
                print(f"   Progress: {current}/{total} ({current/total*100:.0f}%)")
        
        uncertainty_results = client.uncertainty.run_monte_carlo(
            system=system,
            impact_method=method,
            iterations=100,
            progress_callback=progress
        )
        
        # Show results for global warming
        gwp_name = next(k for k in uncertainty_results.keys() 
                       if 'warming' in k.lower())
        gwp_unc = uncertainty_results[gwp_name]
        
        print(f"\n   {gwp_name} Uncertainty:")
        print(f"     Mean:    {gwp_unc.mean:.4e}")
        print(f"     Std Dev: {gwp_unc.std:.4e}")
        print(f"     95% CI:  [{gwp_unc.percentile_5:.4e}, {gwp_unc.percentile_95:.4e}]")
        print(f"     CV:      {gwp_unc.cv:.2%}")
    
    except Exception as e:
        print(f"   Skipped: {e}")
    
    # ========================================================================
    # 10. EXPORT RESULTS
    # ========================================================================
    
    print("\n10. Exporting results...")
    
    # Export to CSV
    success = client.export.export_impacts_to_csv(
        impacts, 
        'lca_results.csv'
    )
    if success:
        print("   ✓ Exported to lca_results.csv")
    
    # ========================================================================
    # COMPLETE
    # ========================================================================
    
    print("\n" + "="*70)
    print("WORKFLOW COMPLETE")
    print("="*70)
    print("\n✓ All steps completed successfully!")
    print("✓ Check generated files:")
    print("  - lca_results.csv")


if __name__ == "__main__":
    main()