#!/usr/bin/env python3
"""
Test script for the Quantum Visualizer 3D Backend
"""

import requests
import json
import time

def test_backend():
    """Test the quantum backend API"""
    base_url = "http://localhost:5000"
    
    print("Testing Quantum Visualizer 3D Backend...")
    print("=" * 50)
    
    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print("✗ Health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to backend. Make sure it's running on port 5000")
        return False
    
    print()
    
    # Test example circuits endpoint
    print("2. Testing example circuits...")
    response = requests.get(f"{base_url}/example_circuits")
    if response.status_code == 200:
        print("✓ Example circuits retrieved")
        examples = response.json()['examples']
        print(f"  Found {len(examples)} example circuits")
    else:
        print("✗ Failed to get example circuits")
        return False
    
    print()
    
    # Test Bell state simulation
    print("3. Testing Bell state simulation...")
    bell_circuit = '''# Bell State
circ = QuantumCircuit(2)
circ.h(0)
circ.cx(0, 1)'''
    
    payload = {
        "qiskit_code": bell_circuit
    }
    
    response = requests.post(f"{base_url}/simulate", 
                           headers={'Content-Type': 'application/json'},
                           data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print("✓ Bell state simulation successful")
            print(f"  Number of qubits: {result['num_qubits']}")
            print(f"  Statevector length: {len(result['statevector'])}")
            print(f"  Marginal probabilities: {len(result['marginal_probabilities'])} qubits")
            
            # Check Bell state properties
            probabilities = result['probabilities']
            expected_nonzero = [0, 3]  # |00⟩ and |11⟩ should have equal probability
            
            print(f"  State probabilities: {[f'{p:.3f}' for p in probabilities]}")
            
            # Verify Bell state entanglement
            if abs(probabilities[0] - 0.5) < 0.001 and abs(probabilities[3] - 0.5) < 0.001:
                print("  ✓ Correct Bell state entanglement detected")
            else:
                print("  ⚠ Unexpected probability distribution")
        else:
            print("✗ Bell state simulation failed")
            print(f"  Error: {result['error']}")
            return False
    else:
        print("✗ Bell state API call failed")
        return False
    
    print()
    
    # Test GHZ state simulation
    print("4. Testing GHZ state simulation...")
    ghz_circuit = '''# GHZ State
circ = QuantumCircuit(3)
circ.h(0)
circ.cx(0, 1)
circ.cx(0, 2)'''
    
    payload = {
        "qiskit_code": ghz_circuit
    }
    
    response = requests.post(f"{base_url}/simulate",
                           headers={'Content-Type': 'application/json'},
                           data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print("✓ GHZ state simulation successful")
            print(f"  Number of qubits: {result['num_qubits']}")
            probabilities = result['probabilities']
            print(f"  State probabilities: {[f'{p:.3f}' for p in probabilities]}")
            
            # Check GHZ state properties (|000⟩ and |111⟩ should have equal probability)
            if abs(probabilities[0] - 0.5) < 0.001 and abs(probabilities[7] - 0.5) < 0.001:
                print("  ✓ Correct GHZ state detected")
            else:
                print("  ⚠ Unexpected probability distribution")
        else:
            print("✗ GHZ state simulation failed")
            print(f"  Error: {result['error']}")
            return False
    else:
        print("✗ GHZ state API call failed")
        return False
    
    print()
    
    # Test superposition state
    print("5. Testing single qubit superposition...")
    superposition_circuit = '''# Superposition
circ = QuantumCircuit(1)
circ.h(0)'''
    
    payload = {
        "qiskit_code": superposition_circuit
    }
    
    response = requests.post(f"{base_url}/simulate",
                           headers={'Content-Type': 'application/json'},
                           data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print("✓ Superposition simulation successful")
            marginal_probs = result['marginal_probabilities'][0]
            print(f"  Qubit 0 - P(|0⟩): {marginal_probs['prob_0']:.3f}, P(|1⟩): {marginal_probs['prob_1']:.3f}")
            
            # Check equal superposition
            if abs(marginal_probs['prob_0'] - 0.5) < 0.001 and abs(marginal_probs['prob_1'] - 0.5) < 0.001:
                print("  ✓ Perfect superposition detected")
            else:
                print("  ⚠ Unexpected superposition probabilities")
        else:
            print("✗ Superposition simulation failed")
            print(f"  Error: {result['error']}")
            return False
    else:
        print("✗ Superposition API call failed")
        return False
    
    print()
    print("=" * 50)
    print("✓ All backend tests passed successfully!")
    print("The Quantum Visualizer 3D Backend is ready for Unity integration.")
    
    return True

if __name__ == "__main__":
    test_backend()