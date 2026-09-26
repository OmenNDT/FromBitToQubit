"""
Physics checks for quantum_analysis (no server needed).

Run with: python -m pytest test_quantum_analysis.py
"""

import json
import math
import os

import pytest
from qiskit import QuantumCircuit

from quantum_analysis import EXAMPLES, MAX_STEPS, analyze_circuit, load_circuit


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


def test_steps_follow_each_gate():
    result = analyze("circ = QuantumCircuit(2)\ncirc.h(0)\ncirc.barrier()\ncirc.cx(0, 1)")
    steps = result['steps']

    # Initial state + H + CX (the barrier is skipped)
    assert [s['gate'] and s['gate']['name'] for s in steps] == [None, 'h', 'cx']
    assert steps[2]['gate']['qubits'] == [0, 1]

    # |00>: nothing entangled
    assert_bloch(steps[0]['qubits'][0], [0, 0, 1])
    # After H: qubit 0 on the equator, still not entangled
    assert_bloch(steps[1]['qubits'][0], [1, 0, 0])
    assert steps[1]['pairs'][0]['concurrence'] == pytest.approx(0, abs=1e-9)
    # After CX: Bell state, entanglement appears exactly here
    assert steps[2]['pairs'][0]['concurrence'] == pytest.approx(1)


def test_last_step_matches_final_state():
    for code in EXAMPLES.values():
        result = analyze(code)
        flatten = lambda sv: [x for amplitude in sv for x in amplitude]
        assert flatten(result['steps'][-1]['statevector']) == pytest.approx(flatten(result['statevector']), abs=1e-9)


def test_gate_params_are_reported():
    result = analyze("circ = QuantumCircuit(1)\ncirc.ry(np.pi/3, 0)")
    assert result['steps'][1]['gate']['params'] == pytest.approx([math.pi / 3])


def test_steps_omitted_for_large_circuits():
    circuit = QuantumCircuit(1)
    for _ in range(MAX_STEPS + 1):
        circuit.x(0)
    result = analyze_circuit(circuit)
    assert result['steps'] is None


def test_measuring_one_bell_qubit_collapses_both():
    result = analyze(EXAMPLES['measure_bell'])
    steps = result['steps']
    assert [s['gate'] and s['gate']['name'] for s in steps] == [None, 'h', 'cx', 'measure', 'measure']

    first = steps[3]
    outcome = first['gate']['outcome']
    assert first['gate']['qubits'] == [0] and first['gate']['clbits'] == [0]
    assert first['clbits'] == [outcome, None]
    # Measuring q0 alone puts q1 into the same definite state: no entanglement left
    z = 1 - 2 * outcome
    for qubit in first['qubits']:
        assert_bloch(qubit, [0, 0, z])
        assert not qubit['entangled']
    # The second measurement must agree with the first
    assert steps[4]['gate']['outcome'] == outcome
    assert result['clbits'] == [outcome, outcome]


def test_measurement_counts_come_from_aer():
    result = analyze(EXAMPLES['measure_bell'])
    counts = result['counts']
    assert set(counts) <= {'00', '11'}
    assert sum(counts.values()) == result['shots']
    assert 0.4 < counts.get('00', 0) / result['shots'] < 0.6


def test_seed_makes_measurement_reproducible():
    code = "circ = QuantumCircuit(5, 5)\ncirc.h([0, 1, 2, 3, 4])\ncirc.measure([0, 1, 2, 3, 4], [0, 1, 2, 3, 4])"
    outcomes = {tuple(analyze_circuit(load_circuit(code), seed=7)['clbits']) for _ in range(3)}
    assert len(outcomes) == 1
    assert analyze_circuit(load_circuit(code), seed=7)['counts'] == analyze_circuit(load_circuit(code), seed=7)['counts']


def test_no_counts_without_measurement():
    assert analyze("circ = QuantumCircuit(1)\ncirc.h(0)")['counts'] is None


def test_reset_returns_qubit_to_zero():
    result = analyze("circ = QuantumCircuit(1)\ncirc.x(0)\ncirc.reset(0)")
    assert_bloch(result['qubits'][0], [0, 0, 1])


LESSONS = json.load(open(os.path.join(os.path.dirname(__file__), 'web', 'lessons.json'), encoding='utf-8'))['lessons']


@pytest.mark.parametrize('lesson', LESSONS, ids=lambda l: l['id'])
def test_lesson_has_one_note_per_step(lesson):
    result = analyze(lesson['code'])
    assert len(lesson['notes']) == len(result['steps'])


def test_teleportation_lesson_moves_the_state_to_q2():
    lesson = next(l for l in LESSONS if l['id'] == 'teleportation')
    steps = analyze(lesson['code'])['steps']
    secret = steps[2]['qubits'][0]['bloch_vector']
    assert steps[-1]['qubits'][2]['bloch_vector'] == pytest.approx(secret, abs=1e-9)


def test_deutsch_lesson_detects_balanced_function():
    lesson = next(l for l in LESSONS if l['id'] == 'deutsch')
    assert analyze(lesson['code'])['clbits'] == [1]
    assert analyze(lesson['code'].replace('circ.cx(0, 1)\n', ''))['clbits'] == [0]
