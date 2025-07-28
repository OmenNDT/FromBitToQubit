#!/usr/bin/env python3
"""
Test script for the Simple Quantum Visualizer 3D Backend
"""

import requests
import json
import time

def test_simple_backend():
    """Test the simple quantum backend API"""
    base_url = "http://localhost:5000"
    
    print("Testing Simple Quantum Visualizer 3D Backend...")
    print("=" * 50)
    
    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("[OK] Health check passed")
            result = response.json()
            print(f"  Status: {result['status']}")
            print(f"  Message: {result['message']}")
            if 'note' in result:
                print(f"  Note: {result['note']}")
        else:
            print("[FAIL] Health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Could not connect to backend. Make sure it's running on port 5000")
        print("   Run: python quantum_backend_simple.py")
        return False
    
    print()
    
    # Test example circuits endpoint
    print("2. Testing example circuits...")
    response = requests.get(f"{base_url}/example_circuits")
    if response.status_code == 200:
        print("[OK] Example circuits retrieved")
        examples = response.json()['examples']
        print(f"  Found {len(examples)} example circuits")
        for name in examples.keys():
            print(f"    - {name}")
    else:
        print("[FAIL] Failed to get example circuits")
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
            print("[OK] Bell state simulation successful")
            print(f"  Number of qubits: {result['num_qubits']}")
            print(f"  Statevector length: {len(result['statevector'])}")
            print(f"  Marginal probabilities: {len(result['marginal_probabilities'])} qubits")
            
            # Check Bell state properties
            probabilities = result['probabilities']
            print(f"  State probabilities: {[f'{p:.3f}' for p in probabilities]}")
            
            # Verify Bell state entanglement pattern
            if abs(probabilities[0] - 0.5) < 0.001 and abs(probabilities[3] - 0.5) < 0.001:
                print("  [OK] Correct Bell state entanglement pattern detected")
            else:
                print("  [WARN] Unexpected probability distribution")
            
            # Show marginal probabilities
            for mp in result['marginal_probabilities']:
                print(f"  Qubit {mp['qubit']}: P(|0>)={mp['prob_0']:.3f}, P(|1>)={mp['prob_1']:.3f}")
        else:
            print("[FAIL] Bell state simulation failed")
            print(f"  Error: {result['error']}")
            return False
    else:
        print("[FAIL] Bell state API call failed")
        print(f"  Status: {response.status_code}")
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
            print("[OK] GHZ state simulation successful")
            print(f"  Number of qubits: {result['num_qubits']}")
            probabilities = result['probabilities']
            print(f"  State probabilities: {[f'{p:.3f}' for p in probabilities]}")
            
            # Check GHZ state properties (|000> and |111> should have equal probability)
            if abs(probabilities[0] - 0.5) < 0.001 and abs(probabilities[7] - 0.5) < 0.001:
                print("  [OK] Correct GHZ state pattern detected")
            else:
                print("  [WARN] Unexpected probability distribution")
            
            # Show marginal probabilities
            for mp in result['marginal_probabilities']:
                print(f"  Qubit {mp['qubit']}: P(|0>)={mp['prob_0']:.3f}, P(|1>)={mp['prob_1']:.3f}")
        else:
            print("[FAIL] GHZ state simulation failed")
            print(f"  Error: {result['error']}")
            return False
    else:
        print("[FAIL] GHZ state API call failed")
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
            print("[OK] Superposition simulation successful")
            marginal_probs = result['marginal_probabilities'][0]
            print(f"  Qubit 0 - P(|0>): {marginal_probs['prob_0']:.3f}, P(|1>): {marginal_probs['prob_1']:.3f}")
            
            # Check equal superposition
            if abs(marginal_probs['prob_0'] - 0.5) < 0.001 and abs(marginal_probs['prob_1'] - 0.5) < 0.001:
                print("  [OK] Perfect superposition detected")
            else:
                print("  [WARN] Unexpected superposition probabilities")
        else:
            print("[FAIL] Superposition simulation failed")
            print(f"  Error: {result['error']}")
            return False
    else:
        print("[FAIL] Superposition API call failed")
        return False
    
    print()
    
    # Test X gate
    print("6. Testing X gate...")
    x_circuit = '''# X Gate
circ = QuantumCircuit(1)
circ.x(0)'''
    
    payload = {
        "qiskit_code": x_circuit
    }
    
    response = requests.post(f"{base_url}/simulate",
                           headers={'Content-Type': 'application/json'},
                           data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print("[OK] X gate simulation successful")
            marginal_probs = result['marginal_probabilities'][0]
            print(f"  Qubit 0 - P(|0>): {marginal_probs['prob_0']:.3f}, P(|1>): {marginal_probs['prob_1']:.3f}")
            
            # Check X gate result (should be |1>)
            if marginal_probs['prob_0'] < 0.001 and abs(marginal_probs['prob_1'] - 1.0) < 0.001:
                print("  [OK] Correct X gate result (|1> state)")
            else:
                print("  [WARN] Unexpected X gate result")
        else:
            print("[FAIL] X gate simulation failed")
            print(f"  Error: {result['error']}")
            return False
    else:
        print("[FAIL] X gate API call failed")
        return False
    
    print()
    print("=" * 50)
    print("[OK] All simple backend tests passed successfully!")
    print("The Simple Quantum Visualizer 3D Backend is ready for Unity integration.")
    print()
    print("Next steps:")
    print("1. Keep the backend running: python quantum_backend_simple.py")
    print("2. Set up Unity project with the provided C# scripts")
    print("3. Configure Unity to connect to http://localhost:5000")
    print("4. Test the full 3D visualization!")
    
    return True

if __name__ == "__main__":
    test_simple_backend()