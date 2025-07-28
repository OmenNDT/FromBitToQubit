#!/usr/bin/env python3
"""
Docker deployment test script for Quantum Visualizer 3D
"""

import requests
import json
import time
import sys
import os

def test_docker_deployment(base_url="http://localhost:5000", timeout=60):
    """Test the Docker deployment of the quantum backend"""
    
    print("Testing Quantum Visualizer 3D Docker Deployment...")
    print("=" * 60)
    print(f"Target URL: {base_url}")
    print()
    
    # Wait for container to be ready
    print("1. Waiting for container to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"[OK] Container is ready after {time.time() - start_time:.1f}s")
                break
        except requests.exceptions.RequestException:
            pass
        
        print("    Waiting for container... (this may take a few minutes for first start)")
        time.sleep(5)
    else:
        print("[FAIL] Container did not start within timeout period")
        print("Check if Docker container is running:")
        print("  docker ps")
        print("  docker logs quantum-visualizer-backend")
        return False
    
    print()
    
    # Test health endpoint
    print("2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print("[OK] Health check passed")
            print(f"    Status: {health_data.get('status')}")
            print(f"    Environment: {health_data.get('environment')}")
            print(f"    Qiskit Available: {health_data.get('qiskit_available')}")
            print(f"    Version: {health_data.get('version')}")
        else:
            print(f"[FAIL] Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Health check error: {e}")
        return False
    
    print()
    
    # Test system info endpoint
    print("3. Testing system info endpoint...")
    try:
        response = requests.get(f"{base_url}/info")
        if response.status_code == 200:
            info_data = response.json()
            print("[OK] System info retrieved")
            system_info = info_data.get('system_info', {})
            print(f"    Python Version: {system_info.get('python_version')}")
            print(f"    Flask Version: {system_info.get('flask_version')}")
            print(f"    Container: {system_info.get('container')}")
            print(f"    Qiskit Available: {system_info.get('qiskit_available')}")
        else:
            print(f"[FAIL] System info failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] System info error: {e}")
        return False
    
    print()
    
    # Test example circuits endpoint
    print("4. Testing example circuits endpoint...")
    try:
        response = requests.get(f"{base_url}/example_circuits")
        if response.status_code == 200:
            examples_data = response.json()
            print("[OK] Example circuits retrieved")
            examples = examples_data.get('examples', {})
            print(f"    Available examples: {len(examples)}")
            for name in examples.keys():
                print(f"      - {name}")
        else:
            print(f"[FAIL] Example circuits failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Example circuits error: {e}")
        return False
    
    print()
    
    # Test quantum simulation
    print("5. Testing quantum simulation endpoint...")
    
    test_circuits = [
        {
            "name": "Bell State",
            "code": '''# Bell State
circ = QuantumCircuit(2)
circ.h(0)
circ.cx(0, 1)''',
            "expected_qubits": 2
        },
        {
            "name": "Superposition",
            "code": '''# Superposition
circ = QuantumCircuit(1)
circ.h(0)''',
            "expected_qubits": 1
        }
    ]
    
    for test_circuit in test_circuits:
        print(f"   Testing {test_circuit['name']}...")
        try:
            payload = {"qiskit_code": test_circuit["code"]}
            response = requests.post(
                f"{base_url}/simulate",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"   [OK] {test_circuit['name']} simulation successful")
                    print(f"        Qubits: {result.get('num_qubits')}")
                    print(f"        Simulation Type: {result.get('simulation_type', 'unknown')}")
                    print(f"        States: {len(result.get('statevector', []))}")
                    
                    # Verify expected number of qubits
                    if result.get('num_qubits') == test_circuit['expected_qubits']:
                        print(f"        [OK] Correct number of qubits")
                    else:
                        print(f"        [WARN] Expected {test_circuit['expected_qubits']} qubits, got {result.get('num_qubits')}")
                else:
                    print(f"   [FAIL] {test_circuit['name']} simulation failed: {result.get('error')}")
                    return False
            else:
                print(f"   [FAIL] {test_circuit['name']} HTTP error {response.status_code}")
                return False
        except Exception as e:
            print(f"   [FAIL] {test_circuit['name']} error: {e}")
            return False
    
    print()
    
    # Test error handling
    print("6. Testing error handling...")
    try:
        payload = {"qiskit_code": "invalid python code"}
        response = requests.post(
            f"{base_url}/simulate",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=10
        )
        
        if response.status_code >= 400:
            result = response.json()
            if not result.get('success') and 'error' in result:
                print("[OK] Error handling works correctly")
                print(f"    Error message: {result['error'][:100]}...")
            else:
                print("[WARN] Error response format unexpected")
        else:
            print("[WARN] Expected error response but got success")
    except Exception as e:
        print(f"[FAIL] Error handling test failed: {e}")
        return False
    
    print()
    
    # Performance test
    print("7. Testing performance...")
    try:
        start_time = time.time()
        payload = {"qiskit_code": "circ = QuantumCircuit(1)\ncirc.h(0)"}
        response = requests.post(
            f"{base_url}/simulate",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=10
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200 and response.json().get('success'):
            print(f"[OK] Performance test passed")
            print(f"    Response time: {response_time:.2f}s")
            if response_time < 5.0:
                print("    [OK] Fast response time")
            else:
                print("    [WARN] Slow response time")
        else:
            print("[FAIL] Performance test failed")
            return False
    except Exception as e:
        print(f"[FAIL] Performance test error: {e}")
        return False
    
    print()
    print("=" * 60)
    print("[OK] All Docker deployment tests passed successfully!")
    print()
    print("Your Quantum Visualizer 3D Docker container is ready for use!")
    print(f"API Base URL: {base_url}")
    print()
    print("Unity Integration:")
    print(f"  Set backendUrl = \"{base_url}\" in QuantumSimulationManager.cs")
    print()
    print("Available endpoints:")
    print(f"  GET  {base_url}/health")
    print(f"  GET  {base_url}/info")
    print(f"  GET  {base_url}/example_circuits")
    print(f"  POST {base_url}/simulate")
    
    return True

def main():
    """Main function"""
    # Check for custom URL
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # Run the test
    success = test_docker_deployment(base_url)
    
    if not success:
        print()
        print("Docker Deployment Test FAILED!")
        print()
        print("Troubleshooting steps:")
        print("1. Check if Docker container is running:")
        print("   docker ps")
        print("2. Check container logs:")
        print("   docker logs quantum-visualizer-backend")
        print("3. Try rebuilding the container:")
        print("   docker-compose down")
        print("   docker-compose up --build")
        print("4. Check Docker system resources:")
        print("   docker system df")
        print("5. Ensure port 5000 is not in use:")
        print("   netstat -an | grep 5000")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()