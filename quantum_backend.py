from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import traceback

from quantum_analysis import EXAMPLES, analyze_circuit, load_circuit

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')

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
        "marginal_probabilities": [{"qubit", "prob_0", "prob_1"}, ...],
        "qubits": [{"qubit", "bloch_vector", "purity", "entropy", "entangled"}, ...],
        "pairs": [{"qubits", "concurrence", "mutual_information"}, ...],
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
        
        circuit = load_circuit(data['qiskit_code'])
        return jsonify(analyze_circuit(circuit))
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Simulation error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/', methods=['GET'])
def web_visualizer():
    """Serve the Three.js web visualizer"""
    return send_from_directory(WEB_DIR, 'index.html')

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
    return jsonify({
        'success': True,
        'examples': EXAMPLES
    })

if __name__ == '__main__':
    print("Starting Quantum Visualizer 3D Backend...")
    print("Available endpoints:")
    print("  POST /simulate - Simulate quantum circuits")
    print("  GET /health - Health check")
    print("  GET /example_circuits - Get example circuits")
    print()
    app.run(host='0.0.0.0', port=5000, debug=True)