# Quantum Visualizer 3D - Setup Guide

## Project Overview

Quantum Visualizer 3D is an interactive 3D visualization tool that helps users "see" and "experience" abstract quantum computing concepts instead of just reading code. The project uses the computational power of Qiskit-Aer as the "brain" and Unity 3D's unlimited graphical flexibility as the "stage".

## Architecture

### Backend (Python)
- **Purpose**: Scientific quantum computation brain
- **Technology**: Python + Flask + Qiskit + Qiskit-Aer
- **Functionality**: 
  - Receives Qiskit code via REST API
  - Executes quantum simulation using statevector_simulator
  - Returns statevector and analysis results in JSON format

### Frontend (Unity)
- **Purpose**: 3D visualization stage
- **Technology**: Unity 3D + C#
- **Functionality**:
  - User interface for inputting Qiskit code
  - Communication with Python backend via UnityWebRequest
  - Real-time 3D visualization of quantum states
  - Interactive qubit representations with visual effects

## Setup Instructions

### 1. Python Backend Setup

#### Prerequisites
- Python 3.8 or higher
- pip package manager

#### Installation
```bash
# Navigate to project directory
cd vk-5eec-quantum-vi

# Create virtual environment (recommended)
python -m venv quantum_env

# Activate virtual environment
# On Windows:
quantum_env\Scripts\activate
# On macOS/Linux:
source quantum_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Running the Backend
```bash
python quantum_backend.py
```

The backend will start on `http://localhost:5000` with the following endpoints:
- `POST /simulate` - Simulate quantum circuits
- `GET /health` - Health check
- `GET /example_circuits` - Get example circuits

#### Testing the Backend
```bash
python test_backend.py
```

### 2. Unity Frontend Setup

#### Prerequisites
- Unity 2022.3 LTS or higher
- Newtonsoft.Json package (available via Unity Package Manager)

#### Setup Steps

1. **Create New Unity Project**:
   - Open Unity Hub
   - Create new 3D project
   - Name it "QuantumVisualizer3D"

2. **Install Required Packages**:
   - Open Unity Package Manager (Window → Package Manager)
   - Install "Newtonsoft Json" package

3. **Import Scripts**:
   - Copy all scripts from `Unity/Assets/Scripts/` to your Unity project's `Assets/Scripts/` folder:
     - `QuantumSimulationManager.cs`
     - `QuantumUI.cs`
     - `QubitVisualizer.cs`
     - `QuantumVisualizer.cs`

4. **Create Scene Setup**:

   **Main Scene Objects**:
   - Create empty GameObject named "QuantumSystem"
   - Attach `QuantumSimulationManager` script
   - Attach `QuantumVisualizer` script

   **UI Setup**:
   - Create Canvas (UI → Canvas)
   - Add UI elements:
     - InputField (TMP) for Qiskit code input
     - Button for "Simulate" action
     - Button for "Clear" action
     - Dropdown (TMP) for example circuits
     - Button for "Load Example"
     - Text (TMP) for status display
     - Text (TMP) for results display
     - ScrollRect for results scrolling

   **UI Manager**:
   - Create empty GameObject named "UIManager"
   - Attach `QuantumUI` script
   - Connect all UI references in inspector

5. **Configure Components**:
   - Set backend URL in QuantumSimulationManager (default: http://localhost:5000)
   - Connect UI references in QuantumUI component
   - Link QuantumSimulationManager and QuantumVisualizer in QuantumUI

## Usage

### 1. Start the Backend
```bash
python quantum_backend.py
```

### 2. Run Unity Scene
- Play the Unity scene
- The system will automatically test backend connection

### 3. Create Quantum Circuits
Enter Qiskit code in the input field, for example:

**Bell State**:
```python
# Bell State (Entanglement)
circ = QuantumCircuit(2)
circ.h(0)
circ.cx(0, 1)
```

**GHZ State**:
```python
# GHZ State (3-qubit entanglement)
circ = QuantumCircuit(3)
circ.h(0)
circ.cx(0, 1)
circ.cx(0, 2)
```

### 4. Visualize Results
- Click "Simulate" to run the quantum circuit
- View 3D visualization with:
  - **Blue spheres**: |0⟩ state
  - **Red spheres**: |1⟩ state  
  - **Purple spheres**: superposition state with dancing particles
  - **Yellow spheres**: entangled qubits with connecting lines
  - **Black dots**: probability position indicators

## Visual Effects Guide

### Qubit States
- **Definite |0⟩**: Blue sphere, black dot at "north pole"
- **Definite |1⟩**: Red sphere, black dot at "south pole"
- **Superposition**: Purple sphere, black dot dancing randomly, particle effects
- **Entanglement**: Yellow/gold color, pulsing, connection lines between qubits

### Animation System
- **Static states**: Smooth dot positioning
- **Superposition**: Random dot movement + particle effects
- **Entanglement**: Synchronized pulsing + connection lines

## API Reference

### Backend Endpoints

#### POST /simulate
Simulate a quantum circuit and return statevector.

**Request**:
```json
{
  "qiskit_code": "circ = QuantumCircuit(2)\\ncirc.h(0)\\ncirc.cx(0, 1)"
}
```

**Response**:
```json
{
  "success": true,
  "statevector": [[0.707, 0.0], [0.0, 0.0], [0.0, 0.0], [0.707, 0.0]],
  "num_qubits": 2,
  "probabilities": [0.5, 0.0, 0.0, 0.5],
  "marginal_probabilities": [
    {"qubit": 0, "prob_0": 0.5, "prob_1": 0.5},
    {"qubit": 1, "prob_0": 0.5, "prob_1": 0.5}
  ],
  "circuit_depth": 2,
  "circuit_size": 2
}
```

#### GET /health
Health check endpoint.

#### GET /example_circuits
Get predefined example circuits.

## Troubleshooting

### Backend Issues
1. **Port 5000 already in use**: Change port in `quantum_backend.py`
2. **Module not found**: Ensure virtual environment is activated and requirements installed
3. **Qiskit errors**: Check Qiskit code syntax

### Unity Issues
1. **JSON parsing errors**: Ensure Newtonsoft.Json package is installed
2. **Network connection**: Check backend URL and firewall settings
3. **Visual artifacts**: Verify material assignments in scripts

### Performance
- Large quantum systems (>5 qubits) may be slow to simulate
- Consider limiting visualization to significant amplitude states
- Unity frame rate may drop with many particle effects

## Development Notes

### Security
- The backend uses `exec()` for code execution with limited globals
- In production, implement proper sandboxing
- Consider code validation and whitelisting

### Extensibility
- Add new visualization effects by extending `QubitVisualizer`
- Implement custom quantum gate visualizations
- Add support for quantum measurements and noise models

### Performance Optimization
- Implement state amplitude thresholding
- Use object pooling for particle effects
- Cache frequently used materials and meshes

## Example Circuits

The system includes several predefined examples:
- **Bell State**: Basic 2-qubit entanglement
- **GHZ State**: 3-qubit entanglement  
- **Superposition**: Single qubit in superposition
- **X Gate**: Simple bit flip operation
- **Quantum Fourier Transform**: Advanced 3-qubit QFT

## Contributing

To add new features:
1. Backend: Extend `quantum_backend.py` with new endpoints
2. Unity: Create new visualization components
3. Test: Add test cases to `test_backend.py`
4. Document: Update this README with new features

## License

See LICENSE file for licensing information.