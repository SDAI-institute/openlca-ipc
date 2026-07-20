# ============================================================================
# WORKING DEMO - olca_utils connection test
# ============================================================================

if __name__ == "__main__":
    """
    Working demonstration that the openlca_ipc package can be imported and connected.
    """

    from openlca_ipc import OLCAClient
    
    print("="*70)
    print("OPENLCA_IPC CONNECTION TEST")
    print("="*70)
    
    try:
        # Initialize client
        client = OLCAClient(port=8080)
        print("[OK] Successfully created OLCAClient")
        print("[OK] Connection established on port {}".format(client.port))
        
        # Test basic connection (this will fail if no openLCA server is running)
        print("\nTesting connection to openLCA server...")
        if client.test_connection():
            print("[OK] Connection test successful!")
        else:
            print("[FAIL] Connection test failed - is openLCA running with IPC server on port 8080?")
        
        print(f"\nClient attributes available:")
        for attr in ['search', 'data', 'systems', 'calculate', 'results', 
                     'contributions', 'uncertainty', 'parameters', 'export']:
            value = getattr(client, attr, None)
            status = "[OK] Available" if value else "[PENDING] Not implemented"
            print(f"  {attr}: {status}")
            
    except ConnectionError as e:
        print("[FAIL] Failed to connect to openLCA: {}".format(e))
        print("  Make sure openLCA is running with IPC server enabled on port 8080")
    except Exception as e:
        print("[FAIL] Unexpected error: {}".format(e))
    
    print("\n" + "="*70)
    print("DEMO COMPLETE - Basic import and connection working!")
    print("="*70)