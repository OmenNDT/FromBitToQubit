using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using Newtonsoft.Json;

[System.Serializable]
public class StatevectorResponse
{
    public bool success;
    public List<List<float>> statevector;  // Complex numbers as [real, imag] pairs
    public int num_qubits;
    public List<float> probabilities;
    public List<MarginalProbability> marginal_probabilities;
    public int circuit_depth;
    public int circuit_size;
    public string error;
    public string traceback;
}

[System.Serializable]
public class MarginalProbability 
{
    public int qubit;
    public float prob_0;
    public float prob_1;
}

[System.Serializable]
public class SimulationRequest
{
    public string qiskit_code;
}

public class QuantumSimulationManager : MonoBehaviour
{
    [Header("Backend Configuration")]
    public string backendUrl = "http://localhost:5000";
    
    [Header("Current Simulation Data")]
    public StatevectorResponse currentSimulation;
    
    [Header("Events")]
    public UnityEngine.Events.UnityEvent<StatevectorResponse> OnSimulationComplete;
    public UnityEngine.Events.UnityEvent<string> OnSimulationError;
    
    private bool isSimulating = false;
    
    public bool IsSimulating => isSimulating;
    
    /// <summary>
    /// Simulate a quantum circuit using the Python backend
    /// </summary>
    /// <param name="qiskitCode">Qiskit circuit code as string</param>
    public void SimulateCircuit(string qiskitCode)
    {
        if (isSimulating)
        {
            Debug.LogWarning("Simulation already in progress. Please wait.");
            return;
        }
        
        if (string.IsNullOrEmpty(qiskitCode))
        {
            OnSimulationError?.Invoke("Qiskit code cannot be empty");
            return;
        }
        
        StartCoroutine(SimulateCircuitCoroutine(qiskitCode));
    }
    
    private IEnumerator SimulateCircuitCoroutine(string qiskitCode)
    {
        isSimulating = true;
        
        Debug.Log($"Starting quantum simulation...\nCode:\n{qiskitCode}");
        
        // Prepare request data
        SimulationRequest requestData = new SimulationRequest
        {
            qiskit_code = qiskitCode
        };
        
        string jsonData = JsonConvert.SerializeObject(requestData);
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonData);
        
        // Create UnityWebRequest
        UnityWebRequest request = new UnityWebRequest($"{backendUrl}/simulate", "POST");
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        
        // Send request
        yield return request.SendWebRequest();
        
        isSimulating = false;
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            try
            {
                string responseText = request.downloadHandler.text;
                Debug.Log($"Simulation response: {responseText}");
                
                StatevectorResponse response = JsonConvert.DeserializeObject<StatevectorResponse>(responseText);
                
                if (response.success)
                {
                    currentSimulation = response;
                    Debug.Log($"Simulation successful! Qubits: {response.num_qubits}, States: {response.statevector.Count}");
                    OnSimulationComplete?.Invoke(response);
                }
                else
                {
                    string errorMessage = $"Simulation failed: {response.error}";
                    if (!string.IsNullOrEmpty(response.traceback))
                    {
                        errorMessage += $"\nTraceback: {response.traceback}";
                    }
                    Debug.LogError(errorMessage);
                    OnSimulationError?.Invoke(response.error);
                }
            }
            catch (Exception e)
            {
                string errorMessage = $"Failed to parse simulation response: {e.Message}";
                Debug.LogError(errorMessage);
                OnSimulationError?.Invoke(errorMessage);
            }
        }
        else
        {
            string errorMessage = $"Network error: {request.error}";
            Debug.LogError(errorMessage);
            OnSimulationError?.Invoke(errorMessage);
        }
        
        request.Dispose();
    }
    
    /// <summary>
    /// Get example circuits from the backend
    /// </summary>
    public void GetExampleCircuits()
    {
        StartCoroutine(GetExampleCircuitsCoroutine());
    }
    
    private IEnumerator GetExampleCircuitsCoroutine()
    {
        UnityWebRequest request = UnityWebRequest.Get($"{backendUrl}/example_circuits");
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log($"Example circuits: {request.downloadHandler.text}");
        }
        else
        {
            Debug.LogError($"Failed to get example circuits: {request.error}");
        }
        
        request.Dispose();
    }
    
    /// <summary>
    /// Test connection to backend
    /// </summary>
    public void TestBackendConnection()
    {
        StartCoroutine(TestConnectionCoroutine());
    }
    
    private IEnumerator TestConnectionCoroutine()
    {
        UnityWebRequest request = UnityWebRequest.Get($"{backendUrl}/health");
        yield return request.SendWebRequest();
        
        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log($"Backend connection successful: {request.downloadHandler.text}");
        }
        else
        {
            Debug.LogError($"Backend connection failed: {request.error}");
        }
        
        request.Dispose();
    }
    
    /// <summary>
    /// Calculate individual qubit probabilities from marginal probabilities
    /// </summary>
    /// <param name="qubitIndex">Index of the qubit (0-based)</param>
    /// <returns>Tuple of (prob_0, prob_1) or null if qubit not found</returns>
    public (float prob0, float prob1)? GetQubitProbabilities(int qubitIndex)
    {
        if (currentSimulation?.marginal_probabilities == null || 
            qubitIndex < 0 || qubitIndex >= currentSimulation.num_qubits)
        {
            return null;
        }
        
        var marginalProb = currentSimulation.marginal_probabilities.Find(mp => mp.qubit == qubitIndex);
        if (marginalProb != null)
        {
            return (marginalProb.prob_0, marginalProb.prob_1);
        }
        
        return null;
    }
    
    /// <summary>
    /// Check if a qubit is in superposition
    /// </summary>
    /// <param name="qubitIndex">Index of the qubit</param>
    /// <param name="threshold">Threshold for considering equal probabilities (default 0.01)</param>
    /// <returns>True if in superposition</returns>
    public bool IsQubitInSuperposition(int qubitIndex, float threshold = 0.01f)
    {
        var probs = GetQubitProbabilities(qubitIndex);
        if (!probs.HasValue) return false;
        
        return Mathf.Abs(probs.Value.prob0 - probs.Value.prob1) < threshold;
    }
    
    /// <summary>
    /// Get the complex amplitude for a specific computational basis state
    /// </summary>
    /// <param name="stateIndex">Index of the computational basis state</param>
    /// <returns>Complex amplitude as (real, imaginary) or null if invalid</returns>
    public (float real, float imag)? GetStateAmplitude(int stateIndex)
    {
        if (currentSimulation?.statevector == null || 
            stateIndex < 0 || stateIndex >= currentSimulation.statevector.Count)
        {
            return null;
        }
        
        var amplitude = currentSimulation.statevector[stateIndex];
        return (amplitude[0], amplitude[1]);
    }
    
    void Start()
    {
        // Test backend connection on start
        TestBackendConnection();
    }
}