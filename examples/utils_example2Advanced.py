# ============================================================================
# COMPLETE USAGE EXAMPLE WITH ADVANCED FEATURES
# ============================================================================

if __name__ == "__main__":
    """
    Complete example demonstrating all advanced features.
    """
    
    from openlca_ipc import OLCAClient
    import matplotlib.pyplot as plt
    
    # Initialize client
    client = OLCAClient(port=8080)
    
    print("="*70)
    print("ADVANCED LCA ANALYSIS EXAMPLE")
    print("="*70)
    
    # Assume we have two systems already created
    pet_system_ref = client.search.find_processes(['PET bottle'])[0]
    pc_system_ref = client.search.find_processes(['PC bottle'])[0]
    method = client.search.find_impact_method(['TRACI'])
    
    # 1. CONTRIBUTION ANALYSIS
    print("\n1. CONTRIBUTION ANALYSIS")
    print("-" * 70)
    
    result = client.calculate.contribution_analysis(pet_system_ref, method)
    
    # Get global warming impact
    impacts = client.results.get_total_impacts(result)
    gwp = next(i for i in impacts if 'warming' in i['name'].lower())
    
    # Top contributors
    top_contribs = client.contributions.get_top_contributors(
        result, gwp['category'], n=5
    )
    
    print(f"\nTop 5 contributors to Global Warming:")
    for i, c in enumerate(top_contribs, 1):
        print(f"  {i}. {c.name[:50]}: {c.share*100:.1f}%")
    
    result.dispose()
    
    # 2. SCENARIO ANALYSIS
    print("\n2. SCENARIO ANALYSIS")
    print("-" * 70)
    
    scenario_results = client.parameters.run_scenario_analysis(
        system=pet_system_ref,
        impact_method=method,
        parameter_name='transport_distance',
        values=[100, 500, 1000, 2000]
    )
    
    print("\nTransport distance sensitivity:")
    for distance, impacts in scenario_results.items():
        gwp = next(i for i in impacts if 'warming' in i['name'].lower())
        print(f"  {distance:4.0f} km: {gwp['amount']:.4e}")
    
    # 3. MONTE CARLO SIMULATION
    print("\n3. UNCERTAINTY ANALYSIS")
    print("-" * 70)
    
    def progress(current, total):
        if current % 200 == 0:
            print(f"  Progress: {current}/{total} ({current/total*100:.0f}%)")
    
    print("\nRunning Monte Carlo simulation (1000 iterations)...")
    uncertainty_results = client.uncertainty.run_monte_carlo(
        system=pet_system_ref,
        impact_method=method,
        iterations=1000,
        progress_callback=progress
    )
    
    # Show uncertainty for global warming
    gwp_name = next(k for k in uncertainty_results.keys() if 'warming' in k.lower())
    gwp_uncertainty = uncertainty_results[gwp_name]
    
    print(f"\nGlobal Warming Uncertainty:")
    print(f"  Mean: {gwp_uncertainty.mean:.4e}")
    print(f"  Std Dev: {gwp_uncertainty.std:.4e}")
    print(f"  95% CI: [{gwp_uncertainty.percentile_5:.4e}, {gwp_uncertainty.percentile_95:.4e}]")
    print(f"  CV: {gwp_uncertainty.cv:.2%}")
    
    # 4. EXPORT RESULTS
    print("\n4. EXPORTING RESULTS")
    print("-" * 70)
    
    # Export comparison
    client.export.export_impacts_to_csv(impacts, 'pet_impacts.csv')
    print("  ✓ Exported impacts to pet_impacts.csv")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)