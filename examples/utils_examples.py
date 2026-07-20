# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example: Complete LCA workflow using the utils library
    
    from openlca_ipc import OLCAClient
    
    # Initialize
    client = OLCAClient(port=8080)
    
    # Test connection
    if not client.test_connection():
        print("Failed to connect to openLCA")
        exit(1)
    
    # Search for materials
    pet_flow = client.search.find_flow(['polyethylene', 'terephthalate', 'granulate'])
    pet_provider = client.search.find_best_provider(pet_flow)
    
    # Create product flow
    pet_bottle = client.data.create_product_flow("PET bottle, 0.5L")
    
    # Create exchanges
    exchanges = [
        client.data.create_exchange(pet_bottle, 0.065, False, True),
        client.data.create_exchange(pet_flow, 0.060, True, provider=pet_provider)
    ]
    
    # Create process
    process = client.data.create_process(
        "PET Bottle Production",
        "Production of 0.5L PET bottle",
        exchanges
    )
    
    # Create product system
    system = client.systems.create_product_system(process)
    
    # Find impact method
    method = client.search.find_impact_method(['TRACI'])
    
    # Calculate
    result = client.calculate.simple_calculation(system, method)
    
    # Analyze results
    impacts = client.results.get_total_impacts(result)
    for impact in impacts[:3]:
        print(f"{impact['name']}: {impact['amount']:.4e}")
    
    # Cleanup
    result.dispose()
    
    print("\n✓ Example complete!")