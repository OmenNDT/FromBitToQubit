"""
Physics checks for quantum_analysis (no server needed).

Run with: python -m pytest test_quantum_analysis.py
"""

import math

import pytest

from quantum_analysis import EXAMPLES, analyze_circuit, load_circuit


def analyze(code):
    return analyze_circuit(load_circuit(code))


def assert_bloch(qubit, expected):
    assert qubit['bloch_vector'] == pytest.approx(expected, abs=1e-9)


def test_ground_state_points_to_north_pole():
    result = analyze("circ = QuantumCircuit(1)")
    assert_bloch(result['qubits'][0], [0, 0, 1])
    assert result['qubits'][0]['purity'] == pytest.approx(1)
    assert not result['qubits'][0]['entangled']


def test_x_gate_points_to_south_pole():
    result = analyze("circ = QuantumCircuit(1)\ncirc.x(0)")
    assert_bloch(result['qubits'][0], [0, 0, -1])
    assert result['marginal_probabilities'][0]['prob_1'] == pytest.approx(1)


def test_plus_and_minus_states_are_distinguished_by_phase():
    plus = analyze("circ = QuantumCircuit(1)\ncirc.h(0)")
    minus = analyze("circ = QuantumCircuit(1)\ncirc.x(0)\ncirc.h(0)")

    # Same measurement probabilities...
    assert plus['probabilities'] == pytest.approx(minus['probabilities'])
    # ...but opposite points on the Bloch sphere
    assert_bloch(plus['qubits'][0], [1, 0, 0])
    assert_bloch(minus['qubits'][0], [-1, 0, 0])


def test_product_superposition_is_not_entangled():
    # |+>|+> has four equally likely outcomes but no entanglement
    result = analyze("circ = QuantumCircuit(2)\ncirc.h(0)\ncirc.h(1)")

    assert all(p == pytest.approx(0.25) for p in result['probabilities'])
    for qubit in result['qubits']:
        assert not qubit['entangled']
        assert_bloch(qubit, [1, 0, 0])
    assert result['pairs'][0]['concurrence'] == pytest.approx(0, abs=1e-9)
    assert result['pairs'][0]['mutual_information'] == pytest.approx(0, abs=1e-9)


def test_bell_state_is_maximally_entangled():
    result = analyze("circ = QuantumCircuit(2)\ncirc.h(0)\ncirc.cx(0, 1)")

    for qubit in result['qubits']:
        assert qubit['entangled']
        assert qubit['purity'] == pytest.approx(0.5)
        assert qubit['entropy'] == pytest.approx(1)
        assert_bloch(qubit, [0, 0, 0])

    pair = result['pairs'][0]
    assert pair['qubits'] == [0, 1]
    assert pair['concurrence'] == pytest.approx(1)
    assert pair['mutual_information'] == pytest.approx(2)


def test_ghz_state_is_multipartite_not_pairwise_entangled():
    result = analyze(
        "circ = QuantumCircuit(3)\ncirc.h(0)\ncirc.cx(0, 1)\ncirc.cx(0, 2)"
    )

    assert all(q['entangled'] for q in result['qubits'])
    assert len(result['pairs']) == 3
    for pair in result['pairs']:
        # Any two GHZ qubits are classically correlated but not entangled with each other
        assert pair['concurrence'] == pytest.approx(0, abs=1e-9)
        assert pair['mutual_information'] == pytest.approx(1)


def test_partially_entangled_state():
    # ry(theta) + cx gives cos(theta/2)|00> + sin(theta/2)|11>, whose concurrence is sin(theta)
    theta = math.pi / 3
    result = analyze(f"circ = QuantumCircuit(2)\ncirc.ry({theta}, 0)\ncirc.cx(0, 1)")

    assert result['pairs'][0]['concurrence'] == pytest.approx(math.sin(theta))
    assert all(q['entangled'] for q in result['qubits'])


def test_qiskit_qubit_order_is_little_endian():
    # X on qubit 1 only -> basis state |10> which is index 2
    result = analyze("circ = QuantumCircuit(2)\ncirc.x(1)")
    assert result['probabilities'][2] == pytest.approx(1)
    assert result['marginal_probabilities'][0]['prob_0'] == pytest.approx(1)
    assert result['marginal_probabilities'][1]['prob_1'] == pytest.approx(1)


def test_missing_circuit_raises():
    with pytest.raises(ValueError):
        load_circuit("x = 1")


@pytest.mark.parametrize('name', sorted(EXAMPLES))
def test_examples_run(name):
    result = analyze(EXAMPLES[name])
    assert result['success']
    assert sum(result['probabilities']) == pytest.approx(1)
