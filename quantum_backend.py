from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
import json
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for Unity communication

@app.route('/simulate', methods=['POST'])
def simulate_quantum_circuit():
    """
    API endpoint to simulate quantum circuits and return statevector
    
    Expected JSON input:
    {
        "qiskit_code": "# Qiskit circuit code as string"
    }
    
    Returns JSON:
    {
        "success": bool,
        "statevector": [[real, imag], ...],
        "num_qubits": int,
        "probabilities": [float, ...],
        "error": str (if success=False)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'qiskit_code' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing qiskit_code parameter'
            }), 400
        
        qiskit_code = data['qiskit_code']
        
        # Create a safe execution environment
        safe_globals = {
            'QuantumCircuit': QuantumCircuit,
            'np': np,
            '__builtins__': {},
        }
        
        safe_locals = {}
        
        # Execute the Qiskit code
        exec(qiskit_code, safe_globals, safe_locals)
        
        # Find the circuit in the executed code
        circuit = None
        for var_name, var_value in safe_locals.items():
            if isinstance(var_value, QuantumCircuit):
                circuit = var_value
                break
        
        if circuit is None:
            return jsonify({
                'success': False,
                'error': 'No QuantumCircuit found in the provided code'
            }), 400
        
        # Get the number of qubits
        num_qubits = circuit.num_qubits
        
        # Simulate using statevector
        initial_state = Statevector.from_int(0, 2**num_qubits)
        final_state = initial_state.evolve(circuit)
        
        # Convert statevector to list format for JSON serialization
        statevector_data = []
        for amplitude in final_state.data:
            statevector_data.append([float(amplitude.real), float(amplitude.imag)])
        
        # Calculate probabilities for each computational basis state
        probabilities = [float(abs(amplitude)**2) for amplitude in final_state.data]
        
        # Calculate marginal probabilities for individual qubits
        marginal_probabilities = []
        for qubit_idx in range(num_qubits):
            prob_0 = 0.0
            prob_1 = 0.0
            
            for state_idx in range(2**num_qubits):
                # Check if qubit_idx is 0 or 1 in this computational basis state
                if (state_idx >> qubit_idx) & 1 == 0:
                    prob_0 += probabilities[state_idx]
                else:
                    prob_1 += probabilities[state_idx]
            
            marginal_probabilities.append({
                'qubit': qubit_idx,
                'prob_0': float(prob_0),
                'prob_1': float(prob_1)
            })
        
        return jsonify({
            'success': True,
            'statevector': statevector_data,
            'num_qubits': num_qubits,
            'probabilities': probabilities,
            'marginal_probabilities': marginal_probabilities,
            'circuit_depth': circuit.depth(),
            'circuit_size': circuit.size()
        })
        
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
        'message': 'Quantum Visualizer 3D Backend is running'
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
circ.x(0)''',
        
        'quantum_fourier_transform': '''# QFT on 3 qubits
circ = QuantumCircuit(3)
circ.h(0)
circ.cp(np.pi/2, 0, 1)
circ.cp(np.pi/4, 0, 2)
circ.h(1)
circ.cp(np.pi/2, 1, 2)
circ.h(2)
circ.swap(0, 2)'''
    }
    
    return jsonify({
        'success': True,
        'examples': examples
    })

if __name__ == '__main__':
    print("Starting Quantum Visualizer 3D Backend...")
    print("Available endpoints:")
    print("  POST /simulate - Simulate quantum circuits")
    print("  GET /health - Health check")
    print("  GET /example_circuits - Get example circuits")
    print()
    app.run(host='0.0.0.0', port=5000, debug=True)