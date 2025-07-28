from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import json
import traceback
import math

app = Flask(__name__)
CORS(app)  # Enable CORS for Unity communication

def simulate_simple_circuit(circuit_type, num_qubits=2):
    """
    Simple quantum circuit simulation without Qiskit dependency
    This is a demonstration version that generates realistic quantum states
    """
    
    if circuit_type == "bell_state":
        # Bell state: (|00⟩ + |11⟩)/√2
        num_qubits = 2
        statevector = [
            [1/math.sqrt(2), 0.0],  # |00⟩
            [0.0, 0.0],             # |01⟩  
            [0.0, 0.0],             # |10⟩
            [1/math.sqrt(2), 0.0]   # |11⟩
        ]
        marginal_probabilities = [
            {"qubit": 0, "prob_0": 0.5, "prob_1": 0.5},
            {"qubit": 1, "prob_0": 0.5, "prob_1": 0.5}
        ]
    
    elif circuit_type == "ghz_state":
        # GHZ state: (|000⟩ + |111⟩)/√2
        num_qubits = 3
        statevector = [
            [1/math.sqrt(2), 0.0],  # |000⟩
            [0.0, 0.0],             # |001⟩
            [0.0, 0.0],             # |010⟩
            [0.0, 0.0],             # |011⟩
            [0.0, 0.0],             # |100⟩
            [0.0, 0.0],             # |101⟩
            [0.0, 0.0],             # |110⟩
            [1/math.sqrt(2), 0.0]   # |111⟩
        ]
        marginal_probabilities = [
            {"qubit": 0, "prob_0": 0.5, "prob_1": 0.5},
            {"qubit": 1, "prob_0": 0.5, "prob_1": 0.5},
            {"qubit": 2, "prob_0": 0.5, "prob_1": 0.5}
        ]
    
    elif circuit_type == "superposition":
        # Single qubit superposition: (|0⟩ + |1⟩)/√2
        num_qubits = 1
        statevector = [
            [1/math.sqrt(2), 0.0],  # |0⟩
            [1/math.sqrt(2), 0.0]   # |1⟩
        ]
        marginal_probabilities = [
            {"qubit": 0, "prob_0": 0.5, "prob_1": 0.5}
        ]
    
    elif circuit_type == "x_gate":
        # X gate: |1⟩
        num_qubits = 1
        statevector = [
            [0.0, 0.0],  # |0⟩
            [1.0, 0.0]   # |1⟩
        ]
        marginal_probabilities = [
            {"qubit": 0, "prob_0": 0.0, "prob_1": 1.0}
        ]
    
    else:
        # Default to |0...0⟩ state
        num_qubits = 2
        statevector = [[1.0, 0.0]] + [[0.0, 0.0]] * (2**num_qubits - 1)
        marginal_probabilities = [
            {"qubit": i, "prob_0": 1.0, "prob_1": 0.0} for i in range(num_qubits)
        ]
    
    # Calculate probabilities from statevector
    probabilities = [sv[0]**2 + sv[1]**2 for sv in statevector]
    
    return {
        "success": True,
        "statevector": statevector,
        "num_qubits": num_qubits,
        "probabilities": probabilities,
        "marginal_probabilities": marginal_probabilities,
        "circuit_depth": 2,
        "circuit_size": 2
    }

@app.route('/simulate', methods=['POST'])
def simulate_quantum_circuit():
    """
    API endpoint to simulate quantum circuits
    """
    try:
        data = request.get_json()
        
        if not data or 'qiskit_code' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing qiskit_code parameter'
            }), 400
        
        qiskit_code = data['qiskit_code'].lower()
        
        # Simple pattern matching to determine circuit type
        if "ghz" in qiskit_code or ("quantumcircuit(3)" in qiskit_code and "cx(0, 2)" in qiskit_code):
            result = simulate_simple_circuit("ghz_state")
        elif "bell" in qiskit_code or ("quantumcircuit(2)" in qiskit_code and "h(0)" in qiskit_code and "cx(0, 1)" in qiskit_code):
            result = simulate_simple_circuit("bell_state")
        elif "h(0)" in qiskit_code and "quantumcircuit(1)" in qiskit_code:
            result = simulate_simple_circuit("superposition")
        elif "x(0)" in qiskit_code:
            result = simulate_simple_circuit("x_gate")
        else:
            result = simulate_simple_circuit("default")
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Simulation error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Quantum Visualizer 3D Backend (Simple Version) is running',
        'note': 'This is a demonstration version without full Qiskit integration'
    })

@app.route('/example_circuits', methods=['GET'])
def get_example_circuits():
    """Return example quantum circuits for testing"""
    examples = {
        'bell_state': '''# Bell State (Entanglement)
circ = QuantumCircuit(2)
circ.h(0)
circ.cx(0, 1)''',
        
        'ghz_state': '''# GHZ State (3-qubit entanglement)
circ = QuantumCircuit(3)
circ.h(0)
circ.cx(0, 1)
circ.cx(0, 2)''',
        
        'superposition': '''# Single qubit superposition
circ = QuantumCircuit(1)
circ.h(0)''',
        
        'x_gate': '''# Simple X gate (bit flip)
circ = QuantumCircuit(1)
circ.x(0)'''
    }
    
    return jsonify({
        'success': True,
        'examples': examples,
        'note': 'Simple demonstration circuits'
    })

if __name__ == '__main__':
    print("Starting Quantum Visualizer 3D Backend (Simple Version)...")
    print("Note: This is a demonstration version without full Qiskit integration")
    print("Available endpoints:")
    print("  POST /simulate - Simulate quantum circuits (pattern matching)")
    print("  GET /health - Health check")
    print("  GET /example_circuits - Get example circuits")
    print()
    app.run(host='0.0.0.0', port=5000, debug=True)