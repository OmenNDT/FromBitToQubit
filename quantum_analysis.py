"""
Quantum state analysis shared by the Flask backends.

All physics is delegated to qiskit.quantum_info; this module only
packages the results into JSON-friendly dictionaries.
"""

from itertools import combinations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import (
    DensityMatrix,
    Pauli,
    Statevector,
    concurrence,
    entropy,
    mutual_information,
    partial_trace,
)

# Numerical tolerance for deciding that a reduced state is mixed (i.e. entangled)
ENTANGLEMENT_TOLERANCE = 1e-6

# Circuits with more gates than this are returned without per-gate steps
MAX_STEPS = 200

_PAULIS = (Pauli('X'), Pauli('Y'), Pauli('Z'))

EXAMPLES = {
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

    'product_superposition': '''# |+>|+> : four equally likely outcomes, yet NOT entangled
circ = QuantumCircuit(2)
circ.h(0)
circ.h(1)''',

    'partial_entanglement': '''# cos(pi/6)|00> + sin(pi/6)|11> : partially entangled
circ = QuantumCircuit(2)
circ.ry(np.pi/3, 0)
circ.cx(0, 1)''',

    'phase_states': '''# |+>, |->, |+i> : same probabilities, different phase
circ = QuantumCircuit(3)
circ.h(0)
circ.x(1)
circ.h(1)
circ.h(2)
circ.s(2)''',

    'quantum_fourier_transform': '''# QFT on 3 qubits
circ = QuantumCircuit(3)
circ.h(0)
circ.cp(np.pi/2, 0, 1)
circ.cp(np.pi/4, 0, 2)
circ.h(1)
circ.cp(np.pi/2, 1, 2)
circ.h(2)
circ.swap(0, 2)''',
}


def load_circuit(qiskit_code):
    """Execute user-provided Qiskit code and return the first QuantumCircuit it defines."""
    safe_globals = {
        'QuantumCircuit': QuantumCircuit,
        'np': np,
        '__builtins__': {},
    }
    safe_locals = {}

    exec(qiskit_code, safe_globals, safe_locals)

    for var_value in safe_locals.values():
        if isinstance(var_value, QuantumCircuit):
            return var_value

    raise ValueError('No QuantumCircuit found in the provided code')


def _clean(value):
    """Round away floating point noise so JSON output stays readable."""
    value = float(np.real(value))
    return 0.0 if abs(value) < 1e-12 else value


def _reduced_state(state, keep):
    """Reduced density matrix of `state` on the qubits listed in `keep`."""
    trace_out = [q for q in range(state.num_qubits) if q not in keep]
    return partial_trace(state, trace_out) if trace_out else DensityMatrix(state)


def analyze_qubits(state):
    """Per-qubit Bloch vector, purity and entanglement flag."""
    qubits = []
    for q in range(state.num_qubits):
        rho = _reduced_state(state, [q])
        purity = _clean(rho.purity())
        qubits.append({
            'qubit': q,
            'bloch_vector': [_clean(rho.expectation_value(p)) for p in _PAULIS],
            'purity': purity,
            'entropy': _clean(entropy(rho, base=2)),
            'entangled': purity < 1 - ENTANGLEMENT_TOLERANCE,
        })
    return qubits


def analyze_pairs(state):
    """Pairwise concurrence (2-qubit entanglement) and mutual information (total correlation)."""
    pairs = []
    for i, j in combinations(range(state.num_qubits), 2):
        rho = _reduced_state(state, [i, j])
        pairs.append({
            'qubits': [i, j],
            'concurrence': _clean(concurrence(rho)),
            'mutual_information': _clean(mutual_information(rho, base=2)),
        })
    return pairs


def analyze_state(state):
    """Statevector, probabilities and entanglement analysis of a single state."""
    # marginal_probabilities is kept for backwards compatibility with the Unity client
    marginal_probabilities = []
    for q in range(state.num_qubits):
        prob_0, prob_1 = state.probabilities([q])
        marginal_probabilities.append({
            'qubit': q,
            'prob_0': _clean(prob_0),
            'prob_1': _clean(prob_1),
        })

    return {
        'statevector': [[_clean(a.real), _clean(a.imag)] for a in state.data],
        'probabilities': [_clean(p) for p in state.probabilities()],
        'marginal_probabilities': marginal_probabilities,
        'qubits': analyze_qubits(state),
        'pairs': analyze_pairs(state),
    }


def _param_value(param):
    try:
        return float(param)
    except (TypeError, ValueError):
        return str(param)


def analyze_steps(circuit, initial_state):
    """
    State after each gate, starting with the initial state.

    Barriers do not change the state and are skipped. Returns None for circuits
    larger than MAX_STEPS to keep the response size bounded.
    """
    if circuit.size() > MAX_STEPS:
        return None

    state = initial_state
    steps = [{'gate': None, **analyze_state(state)}]
    for instruction in circuit.data:
        operation = instruction.operation
        if operation.name == 'barrier':
            continue

        qubits = [circuit.find_bit(q).index for q in instruction.qubits]
        state = state.evolve(operation, qargs=qubits)
        steps.append({
            'gate': {
                'name': operation.name,
                'qubits': qubits,
                'params': [_param_value(p) for p in operation.params],
            },
            **analyze_state(state),
        })
    return steps


def analyze_circuit(circuit):
    """Simulate `circuit` from |0...0> and return the full analysis dictionary."""
    num_qubits = circuit.num_qubits
    initial_state = Statevector.from_int(0, 2**num_qubits)
    state = initial_state.evolve(circuit)

    return {
        'success': True,
        'num_qubits': num_qubits,
        **analyze_state(state),
        'steps': analyze_steps(circuit, initial_state),
        'circuit_depth': circuit.depth(),
        'circuit_size': circuit.size(),
    }
