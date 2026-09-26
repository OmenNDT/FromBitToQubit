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

_PAULIS = (Pauli('X'), Pauli('Y'), Pauli('Z'))


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


def analyze_circuit(circuit):
    """Simulate `circuit` from |0...0> and return the full analysis dictionary."""
    num_qubits = circuit.num_qubits
    state = Statevector.from_int(0, 2**num_qubits).evolve(circuit)

    probabilities = [_clean(p) for p in state.probabilities()]

    # Kept for backwards compatibility with the Unity client
    marginal_probabilities = []
    for q in range(num_qubits):
        prob_0, prob_1 = state.probabilities([q])
        marginal_probabilities.append({
            'qubit': q,
            'prob_0': _clean(prob_0),
            'prob_1': _clean(prob_1),
        })

    return {
        'success': True,
        'statevector': [[_clean(a.real), _clean(a.imag)] for a in state.data],
        'num_qubits': num_qubits,
        'probabilities': probabilities,
        'marginal_probabilities': marginal_probabilities,
        'qubits': analyze_qubits(state),
        'pairs': analyze_pairs(state),
        'circuit_depth': circuit.depth(),
        'circuit_size': circuit.size(),
    }
