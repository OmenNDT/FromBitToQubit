using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class QuantumUI : MonoBehaviour
{
    [Header("UI References")]
    [SerializeField] private TMP_InputField qiskitCodeInput;
    [SerializeField] private Button simulateButton;
    [SerializeField] private Button clearButton;
    [SerializeField] private TMP_Dropdown exampleDropdown;
    [SerializeField] private Button loadExampleButton;
    [SerializeField] private TMP_Text statusText;
    [SerializeField] private TMP_Text resultsText;
    [SerializeField] private ScrollRect resultsScrollRect;
    
    [Header("Simulation Manager")]
    [SerializeField] private QuantumSimulationManager simulationManager;
    
    [Header("Visualization")]
    [SerializeField] private QuantumVisualizer quantumVisualizer;
    
    private Dictionary<string, string> exampleCircuits = new Dictionary<string, string>
    {
        { "Bell State", @"# Bell State (Entanglement)
circ = QuantumCircuit(2)
circ.h(0)
circ.cx(0, 1)" },
        
        { "GHZ State", @"# GHZ State (3-qubit entanglement)  
circ = QuantumCircuit(3)
circ.h(0)
circ.cx(0, 1)
circ.cx(0, 2)" },
        
        { "Superposition", @"# Single qubit superposition
circ = QuantumCircuit(1)
circ.h(0)" },
        
        { "X Gate", @"# Simple X gate (bit flip)
circ = QuantumCircuit(1)
circ.x(0)" },
        
        { "Quantum Fourier Transform", @"# QFT on 3 qubits
import numpy as np
circ = QuantumCircuit(3)
circ.h(0)
circ.cp(np.pi/2, 0, 1)
circ.cp(np.pi/4, 0, 2)
circ.h(1)
circ.cp(np.pi/2, 1, 2)
circ.h(2)
circ.swap(0, 2)" }
    };
    
    void Start()
    {
        SetupUI();
        SetupEventListeners();
        PopulateExampleDropdown();
        
        // Set default example
        LoadExample("Bell State");
    }
    
    void SetupUI()
    {
        if (simulateButton != null)
            simulateButton.interactable = true;
            
        if (statusText != null)
            statusText.text = "Ready to simulate quantum circuits";
            
        if (resultsText != null)
            resultsText.text = "Results will appear here after simulation...";
    }
    
    void SetupEventListeners()
    {
        if (simulateButton != null)
            simulateButton.onClick.AddListener(OnSimulateClick);
            
        if (clearButton != null)
            clearButton.onClick.AddListener(OnClearClick);
            
        if (loadExampleButton != null)
            loadExampleButton.onClick.AddListener(OnLoadExampleClick);
            
        if (simulationManager != null)
        {
            simulationManager.OnSimulationComplete.AddListener(OnSimulationComplete);
            simulationManager.OnSimulationError.AddListener(OnSimulationError);
        }
    }
    
    void PopulateExampleDropdown()
    {
        if (exampleDropdown == null) return;
        
        exampleDropdown.ClearOptions();
        
        var options = new List<TMP_Dropdown.OptionData>();
        foreach (var example in exampleCircuits.Keys)
        {
            options.Add(new TMP_Dropdown.OptionData(example));
        }
        
        exampleDropdown.AddOptions(options);
    }
    
    void OnSimulateClick()
    {
        if (simulationManager == null)
        {
            Debug.LogError("QuantumSimulationManager not assigned!");
            return;
        }
        
        if (qiskitCodeInput == null || string.IsNullOrEmpty(qiskitCodeInput.text))
        {
            UpdateStatusText("Please enter some Qiskit code to simulate", Color.red);
            return;
        }
        
        string code = qiskitCodeInput.text;
        
        // Update UI for simulation start
        UpdateStatusText("Simulating quantum circuit...", Color.yellow);
        simulateButton.interactable = false;
        
        // Start simulation
        simulationManager.SimulateCircuit(code);
    }
    
    void OnClearClick()
    {
        if (qiskitCodeInput != null)
            qiskitCodeInput.text = "";
            
        if (resultsText != null)
            resultsText.text = "Results will appear here after simulation...";
            
        UpdateStatusText("Ready to simulate quantum circuits", Color.white);
    }
    
    void OnLoadExampleClick()
    {
        if (exampleDropdown == null) return;
        
        string selectedExample = exampleDropdown.options[exampleDropdown.value].text;
        LoadExample(selectedExample);
    }
    
    void LoadExample(string exampleName)
    {
        if (exampleCircuits.ContainsKey(exampleName) && qiskitCodeInput != null)
        {
            qiskitCodeInput.text = exampleCircuits[exampleName];
            UpdateStatusText($"Loaded example: {exampleName}", Color.green);
        }
    }
    
    void OnSimulationComplete(StatevectorResponse response)
    {
        // Re-enable simulate button
        simulateButton.interactable = true;
        
        // Update status
        UpdateStatusText($"Simulation complete! {response.num_qubits} qubits, {response.statevector.Count} states", Color.green);
        
        // Display results
        DisplayResults(response);
        
        // Update visualization
        if (quantumVisualizer != null)
        {
            quantumVisualizer.VisualizeStatevector(response);
        }
    }
    
    void OnSimulationError(string error)
    {
        // Re-enable simulate button
        simulateButton.interactable = true;
        
        // Update status
        UpdateStatusText($"Simulation failed: {error}", Color.red);
        
        // Clear results
        if (resultsText != null)
            resultsText.text = $"Error: {error}";
    }
    
    void DisplayResults(StatevectorResponse response)
    {
        if (resultsText == null) return;
        
        System.Text.StringBuilder sb = new System.Text.StringBuilder();
        
        sb.AppendLine($"=== Quantum Circuit Simulation Results ===");
        sb.AppendLine($"Number of Qubits: {response.num_qubits}");
        sb.AppendLine($"Circuit Depth: {response.circuit_depth}");
        sb.AppendLine($"Circuit Size: {response.circuit_size}");
        sb.AppendLine();
        
        // Display marginal probabilities
        sb.AppendLine("Individual Qubit Probabilities:");
        foreach (var marginal in response.marginal_probabilities)
        {
            sb.AppendLine($"  Qubit {marginal.qubit}: P(|0⟩) = {marginal.prob_0:F3}, P(|1⟩) = {marginal.prob_1:F3}");
            
            // Check for superposition
            if (Mathf.Abs(marginal.prob_0 - marginal.prob_1) < 0.01f)
            {
                sb.AppendLine($"    → In superposition! ⚛️");
            }
            else if (marginal.prob_0 > 0.99f)
            {
                sb.AppendLine($"    → Definitely |0⟩");
            }
            else if (marginal.prob_1 > 0.99f)
            {
                sb.AppendLine($"    → Definitely |1⟩");
            }
        }
        
        sb.AppendLine();
        
        // Display computational basis states with significant probability
        sb.AppendLine("Computational Basis States (P > 0.001):");
        for (int i = 0; i < response.probabilities.Count; i++)
        {
            if (response.probabilities[i] > 0.001f)
            {
                string binaryState = System.Convert.ToString(i, 2).PadLeft(response.num_qubits, '0');
                sb.AppendLine($"  |{binaryState}⟩: {response.probabilities[i]:F3}");
            }
        }
        
        sb.AppendLine();
        
        // Display complex amplitudes for significant states
        sb.AppendLine("Complex Amplitudes (|amplitude| > 0.03):");
        for (int i = 0; i < response.statevector.Count; i++)
        {
            float real = response.statevector[i][0];
            float imag = response.statevector[i][1];
            float magnitude = Mathf.Sqrt(real * real + imag * imag);
            
            if (magnitude > 0.03f)
            {
                string binaryState = System.Convert.ToString(i, 2).PadLeft(response.num_qubits, '0');
                string sign = imag >= 0 ? "+" : "";
                sb.AppendLine($"  |{binaryState}⟩: {real:F3} {sign} {imag:F3}i (|amp| = {magnitude:F3})");
            }
        }
        
        resultsText.text = sb.ToString();
        
        // Scroll to top of results
        if (resultsScrollRect != null)
        {
            Canvas.ForceUpdateCanvases();
            resultsScrollRect.verticalNormalizedPosition = 1f;
        }
    }
    
    void UpdateStatusText(string message, Color color)
    {
        if (statusText != null)
        {
            statusText.text = message;
            statusText.color = color;
        }
        
        Debug.Log($"Status: {message}");
    }
}