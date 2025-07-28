using UnityEngine;
using System.Collections.Generic;
using System.Linq;

public class QuantumVisualizer : MonoBehaviour
{
    [Header("Visualization Settings")]
    [SerializeField] private GameObject qubitPrefab;
    [SerializeField] private float qubitSpacing = 2f;
    [SerializeField] private float entanglementThreshold = 0.01f;
    
    [Header("Materials")]
    [SerializeField] private Material state0Material;
    [SerializeField] private Material state1Material;
    [SerializeField] private Material superpositionMaterial;
    [SerializeField] private Material entangledMaterial;
    
    [Header("Current Visualization")]
    public List<QubitVisualizer> activeQubits = new List<QubitVisualizer>();
    public StatevectorResponse currentSimulation;
    
    private Camera mainCamera;
    
    void Awake()
    {
        mainCamera = Camera.main;
        if (mainCamera == null)
            mainCamera = FindObjectOfType<Camera>();
    }
    
    /// <summary>
    /// Main method to visualize a quantum statevector
    /// </summary>
    /// <param name="simulation">The simulation results from the backend</param>
    public void VisualizeStatevector(StatevectorResponse simulation)
    {
        if (simulation == null || !simulation.success)
        {
            Debug.LogError("Invalid simulation data");
            return;
        }
        
        currentSimulation = simulation;
        
        Debug.Log($"Visualizing {simulation.num_qubits} qubits with {simulation.statevector.Count} states");
        
        // Clear existing visualization
        ClearVisualization();
        
        // Create qubits
        CreateQubits(simulation.num_qubits);
        
        // Update qubit visualizations
        UpdateQubitVisualizations(simulation);
        
        // Detect and visualize entanglement
        DetectAndVisualizeEntanglement(simulation);
        
        // Position camera to view all qubits
        PositionCamera();
    }
    
    /// <summary>
    /// Clear the current visualization
    /// </summary>
    void ClearVisualization()
    {
        foreach (var qubit in activeQubits)
        {
            if (qubit != null)
            {
                qubit.RemoveConnection();
                DestroyImmediate(qubit.gameObject);
            }
        }
        activeQubits.Clear();
    }
    
    /// <summary>
    /// Create visual representations for each qubit
    /// </summary>
    /// <param name="numQubits">Number of qubits to create</param>
    void CreateQubits(int numQubits)
    {
        for (int i = 0; i < numQubits; i++)
        {
            Vector3 position = CalculateQubitPosition(i, numQubits);
            GameObject qubitObject = CreateQubitObject(i, position);
            
            QubitVisualizer qubitVis = qubitObject.GetComponent<QubitVisualizer>();
            if (qubitVis == null)
            {
                qubitVis = qubitObject.AddComponent<QubitVisualizer>();
            }
            
            qubitVis.qubitIndex = i;
            SetupQubitMaterials(qubitVis);
            
            activeQubits.Add(qubitVis);
        }
    }
    
    /// <summary>
    /// Calculate the 3D position for a qubit
    /// </summary>
    /// <param name="qubitIndex">Index of the qubit</param>
    /// <param name="totalQubits">Total number of qubits</param>
    /// <returns>3D position for the qubit</returns>
    Vector3 CalculateQubitPosition(int qubitIndex, int totalQubits)
    {
        if (totalQubits == 1)
        {
            return Vector3.zero;
        }
        else if (totalQubits == 2)
        {
            // Side by side
            return new Vector3((qubitIndex - 0.5f) * qubitSpacing, 0, 0);
        }
        else if (totalQubits == 3)
        {
            // Triangle formation
            float angle = qubitIndex * 2f * Mathf.PI / 3f;
            return new Vector3(
                Mathf.Cos(angle) * qubitSpacing,
                0,
                Mathf.Sin(angle) * qubitSpacing
            );
        }
        else
        {
            // Circular arrangement for more qubits
            float angle = qubitIndex * 2f * Mathf.PI / totalQubits;
            float radius = qubitSpacing * Mathf.Max(1f, totalQubits / 4f);
            return new Vector3(
                Mathf.Cos(angle) * radius,
                0,
                Mathf.Sin(angle) * radius
            );
        }
    }
    
    /// <summary>
    /// Create a qubit GameObject at the specified position
    /// </summary>
    GameObject CreateQubitObject(int qubitIndex, Vector3 position)
    {
        GameObject qubitObject;
        
        if (qubitPrefab != null)
        {
            qubitObject = Instantiate(qubitPrefab, position, Quaternion.identity, transform);
        }
        else
        {
            // Create basic qubit from primitives
            qubitObject = new GameObject($"Qubit_{qubitIndex}");
            qubitObject.transform.SetParent(transform);
            qubitObject.transform.position = position;
            
            // Create sphere
            GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            sphere.transform.SetParent(qubitObject.transform);
            sphere.transform.localPosition = Vector3.zero;
            sphere.name = "Sphere";
            
            // Create black dot
            GameObject dot = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            dot.transform.SetParent(qubitObject.transform);
            dot.transform.localPosition = Vector3.up * 0.5f;
            dot.transform.localScale = Vector3.one * 0.1f;
            dot.name = "BlackDot";
            
            // Create line renderer for connections
            LineRenderer lineRenderer = qubitObject.AddComponent<LineRenderer>();
            lineRenderer.enabled = false;
        }
        
        qubitObject.name = $"Qubit_{qubitIndex}";
        return qubitObject;
    }
    
    /// <summary>
    /// Setup materials for a qubit visualizer
    /// </summary>
    void SetupQubitMaterials(QubitVisualizer qubit)
    {
        // If materials are not assigned, create default ones
        if (state0Material == null)
        {
            state0Material = CreateMaterial(Color.blue, "State0Material");
        }
        if (state1Material == null)
        {
            state1Material = CreateMaterial(Color.red, "State1Material");
        }
        if (superpositionMaterial == null)
        {
            superpositionMaterial = CreateMaterial(new Color(0.8f, 0.4f, 1f), "SuperpositionMaterial");
        }
        if (entangledMaterial == null)
        {
            entangledMaterial = CreateMaterial(Color.yellow, "EntangledMaterial");
        }
        
        // Note: QubitVisualizer will access these materials directly
        // This is a design choice - in a production system, you might want to pass them explicitly
    }
    
    /// <summary>
    /// Create a material with the specified color
    /// </summary>
    Material CreateMaterial(Color color, string name)
    {
        Material material = new Material(Shader.Find("Standard"));
        material.color = color;
        material.name = name;
        return material;
    }
    
    /// <summary>
    /// Update all qubit visualizations based on simulation results
    /// </summary>
    void UpdateQubitVisualizations(StatevectorResponse simulation)
    {
        for (int i = 0; i < activeQubits.Count && i < simulation.marginal_probabilities.Count; i++)
        {
            var marginalProb = simulation.marginal_probabilities[i];
            bool isEntangled = DetectQubitEntanglement(i, simulation);
            
            activeQubits[i].UpdateVisualization(
                marginalProb.prob_0,
                marginalProb.prob_1,
                isEntangled
            );
        }
    }
    
    /// <summary>
    /// Detect if a specific qubit is entangled with others
    /// </summary>
    bool DetectQubitEntanglement(int qubitIndex, StatevectorResponse simulation)
    {
        // For now, use a simple heuristic: if the system has significant probability
        // for multiple computational basis states, and this qubit participates
        // in those states differently, it might be entangled
        
        int significantStates = 0;
        for (int i = 0; i < simulation.probabilities.Count; i++)
        {
            if (simulation.probabilities[i] > entanglementThreshold)
            {
                significantStates++;
            }
        }
        
        // If there are multiple significant states and more than one qubit, likely entangled
        return significantStates > 1 && simulation.num_qubits > 1;
    }
    
    /// <summary>
    /// Detect and visualize entanglement between qubits
    /// </summary>
    void DetectAndVisualizeEntanglement(StatevectorResponse simulation)
    {
        if (simulation.num_qubits < 2) return;
        
        // Find pairs of qubits that show strong correlation
        for (int i = 0; i < activeQubits.Count - 1; i++)
        {
            for (int j = i + 1; j < activeQubits.Count; j++)
            {
                float correlation = CalculateQubitCorrelation(i, j, simulation);
                
                if (correlation > 0.5f) // Strong correlation threshold
                {
                    activeQubits[i].CreateConnectionTo(activeQubits[j], correlation);
                }
            }
        }
    }
    
    /// <summary>
    /// Calculate correlation between two qubits based on their joint probabilities
    /// </summary>
    float CalculateQubitCorrelation(int qubit1, int qubit2, StatevectorResponse simulation)
    {
        // This is a simplified correlation measure
        // In a more sophisticated system, you would calculate mutual information
        // or quantum mutual information
        
        float correlation = 0f;
        int numStates = simulation.probabilities.Count;
        
        // Look for states where both qubits have the same value (00 or 11 patterns)
        for (int stateIndex = 0; stateIndex < numStates; stateIndex++)
        {
            bool qubit1State = ((stateIndex >> qubit1) & 1) == 1;
            bool qubit2State = ((stateIndex >> qubit2) & 1) == 1;
            
            if (qubit1State == qubit2State) // Same state
            {
                correlation += simulation.probabilities[stateIndex];
            }
        }
        
        // Normalize: perfect correlation = 1, no correlation = 0.5, anti-correlation = 0
        return Mathf.Abs(correlation - 0.5f) * 2f;
    }
    
    /// <summary>
    /// Position the camera to view all qubits nicely
    /// </summary>
    void PositionCamera()
    {
        if (mainCamera == null || activeQubits.Count == 0) return;
        
        // Calculate bounds of all qubits
        Bounds bounds = new Bounds(activeQubits[0].transform.position, Vector3.zero);
        foreach (var qubit in activeQubits)
        {
            bounds.Encapsulate(qubit.transform.position);
        }
        
        // Position camera to view all qubits
        float distance = Mathf.Max(bounds.size.x, bounds.size.z) * 1.5f + 3f;
        Vector3 cameraPosition = bounds.center + new Vector3(0, distance * 0.7f, -distance);
        
        mainCamera.transform.position = cameraPosition;
        mainCamera.transform.LookAt(bounds.center);
    }
    
    /// <summary>
    /// Get information about the current visualization
    /// </summary>
    public string GetVisualizationInfo()
    {
        if (currentSimulation == null) return "No active visualization";
        
        var info = $"Visualizing {currentSimulation.num_qubits} qubits\n";
        
        for (int i = 0; i < activeQubits.Count; i++)
        {
            var qubit = activeQubits[i];
            info += $"Qubit {i}: P(|0⟩)={qubit.prob0:F3}, P(|1⟩)={qubit.prob1:F3}";
            if (qubit.isInSuperposition) info += " [Superposition]";
            if (qubit.isEntangled) info += " [Entangled]";
            info += "\n";
        }
        
        return info;
    }
    
    void OnDrawGizmos()
    {
        // Draw connection lines between entangled qubits
        Gizmos.color = Color.yellow;
        for (int i = 0; i < activeQubits.Count - 1; i++)
        {
            for (int j = i + 1; j < activeQubits.Count; j++)
            {
                if (activeQubits[i].isEntangled && activeQubits[j].isEntangled)
                {
                    Gizmos.DrawLine(activeQubits[i].transform.position, activeQubits[j].transform.position);
                }
            }
        }
    }
}