from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import traceback
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')

app = Flask(__name__, static_folder=WEB_DIR, static_url_path='')
CORS(app)  # Enable CORS for Unity communication

# Configuration from environment variables
HOST = os.getenv('FLASK_HOST', '0.0.0.0')
PORT = int(os.getenv('FLASK_PORT', 5000))
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Try to import Qiskit, fall back to simple simulation if not available
try:
    from quantum_analysis import EXAMPLES, analyze_circuit, load_circuit
    QISKIT_AVAILABLE = True
    logger.info("Qiskit is available - using full quantum simulation")
except ImportError:
    QISKIT_AVAILABLE = False
    logger.warning("Qiskit not available - using simplified simulation")

def simulate_with_qiskit(qiskit_code, seed=None):
    """Full Qiskit simulation"""
    try:
        result = analyze_circuit(load_circuit(qiskit_code), seed=seed)
        result['simulation_type'] = 'qiskit'
        return result

    except Exception as e:
        logger.error(f"Qiskit simulation error: {str(e)}")
        raise

def simulate_simple_circuit(qiskit_code):
    """Simplified simulation for demonstration"""
    import math
    
    qiskit_code_lower = qiskit_code.lower()
    
    if "bell" in qiskit_code_lower or ("h(0)" in qiskit_code_lower and "cx(0, 1)" in qiskit_code_lower):
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
        circuit_type = "bell_state"
    
    elif "ghz" in qiskit_code_lower or ("quantumcircuit(3)" in qiskit_code_lower and "cx(0, 2)" in qiskit_code_lower):
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
        circuit_type = "ghz_state"
    
    elif "h(0)" in qiskit_code_lower and "quantumcircuit(1)" in qiskit_code_lower:
        # Single qubit superposition: (|0⟩ + |1⟩)/√2
        num_qubits = 1
        statevector = [
            [1/math.sqrt(2), 0.0],  # |0⟩
            [1/math.sqrt(2), 0.0]   # |1⟩
        ]
        marginal_probabilities = [
            {"qubit": 0, "prob_0": 0.5, "prob_1": 0.5}
        ]
        circuit_type = "superposition"
    
    elif "x(0)" in qiskit_code_lower:
        # X gate: |1⟩
        num_qubits = 1
        statevector = [
            [0.0, 0.0],  # |0⟩
            [1.0, 0.0]   # |1⟩
        ]
        marginal_probabilities = [
            {"qubit": 0, "prob_0": 0.0, "prob_1": 1.0}
        ]
        circuit_type = "x_gate"
    
    else:
        # Default to |0...0⟩ state
        num_qubits = 2
        statevector = [[1.0, 0.0]] + [[0.0, 0.0]] * (2**num_qubits - 1)
        marginal_probabilities = [
            {"qubit": i, "prob_0": 1.0, "prob_1": 0.0} for i in range(num_qubits)
        ]
        circuit_type = "default"
    
    # Calculate probabilities from statevector
    probabilities = [sv[0]**2 + sv[1]**2 for sv in statevector]
    
    return {
        'success': True,
        'statevector': statevector,
        'num_qubits': num_qubits,
        'probabilities': probabilities,
        'marginal_probabilities': marginal_probabilities,
        'circuit_depth': 2,
        'circuit_size': 2,
        'simulation_type': 'simple',
        'circuit_type': circuit_type
    }

@app.route('/simulate', methods=['POST'])
def simulate_quantum_circuit():
    """API endpoint to simulate quantum circuits"""
    try:
        data = request.get_json()
        
        if not data or 'qiskit_code' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing qiskit_code parameter'
            }), 400
        
        qiskit_code = data['qiskit_code']
        logger.info(f"Simulating circuit: {qiskit_code[:100]}...")
        
        if QISKIT_AVAILABLE:
            result = simulate_with_qiskit(qiskit_code, seed=data.get('seed'))
        else:
            result = simulate_simple_circuit(qiskit_code)
        
        logger.info(f"Simulation successful: {result.get('num_qubits')} qubits, type: {result.get('simulation_type')}")
        return jsonify(result)
        
    except Exception as e:
        error_msg = f'Simulation error: {str(e)}'
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg,
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
        'message': 'Quantum Visualizer 3D Backend is running',
        'timestamp': datetime.utcnow().isoformat(),
        'qiskit_available': QISKIT_AVAILABLE,
        'version': '1.0.0',
        'environment': 'docker'
    })

@app.route('/info', methods=['GET'])
def get_info():
    """Get system information"""
    return jsonify({
        'success': True,
        'system_info': {
            'qiskit_available': QISKIT_AVAILABLE,
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'flask_version': getattr(__import__('flask'), '__version__', 'unknown'),
            'numpy_available': True,
            'container': True,
            'host': HOST,
            'port': PORT
        }
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
    
    if QISKIT_AVAILABLE:
        examples = EXAMPLES

    return jsonify({
        'success': True,
        'examples': examples,
        'qiskit_available': QISKIT_AVAILABLE
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /health',
            'GET /info', 
            'GET /example_circuits',
            'POST /simulate'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    logger.info("Starting Quantum Visualizer 3D Backend (Docker Version)...")
    logger.info(f"Qiskit available: {QISKIT_AVAILABLE}")
    logger.info("Available endpoints:")
    logger.info("  POST /simulate - Simulate quantum circuits")
    logger.info("  GET /health - Health check")
    logger.info("  GET /info - System information")
    logger.info("  GET /example_circuits - Get example circuits")
    logger.info(f"Starting server on {HOST}:{PORT}")
    
    app.run(host=HOST, port=PORT, debug=DEBUG)