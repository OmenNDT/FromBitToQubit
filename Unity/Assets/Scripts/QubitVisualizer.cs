using UnityEngine;
using System.Collections;

public class QubitVisualizer : MonoBehaviour
{
    [Header("Visual Components")]
    [SerializeField] private GameObject sphere;
    [SerializeField] private GameObject blackDot;
    [SerializeField] private LineRenderer connectionLine;
    [SerializeField] private ParticleSystem superpositionEffect;
    
    [Header("Materials")]
    [SerializeField] private Material state0Material;  // Blue for |0⟩
    [SerializeField] private Material state1Material;  // Red for |1⟩
    [SerializeField] private Material superpositionMaterial;  // Purple for superposition
    [SerializeField] private Material entangledMaterial;  // Gold for entanglement
    
    [Header("Animation Settings")]
    [SerializeField] private float rotationSpeed = 90f;
    [SerializeField] private float pulseSpeed = 2f;
    [SerializeField] private float superpositionAnimationSpeed = 3f;
    
    [Header("State Information")]
    public int qubitIndex;
    public float prob0 = 0.5f;
    public float prob1 = 0.5f;
    public bool isInSuperposition = false;
    public bool isEntangled = false;
    
    private Renderer sphereRenderer;
    private Renderer dotRenderer;
    private Vector3 originalDotPosition;
    private Vector3 originalSphereScale;
    private Coroutine currentAnimation;
    
    void Awake()
    {
        SetupComponents();
    }
    
    void SetupComponents()
    {
        // Get or create sphere
        if (sphere == null)
        {
            sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            sphere.transform.SetParent(transform);
            sphere.transform.localPosition = Vector3.zero;
        }
        sphereRenderer = sphere.GetComponent<Renderer>();
        originalSphereScale = sphere.transform.localScale;
        
        // Get or create black dot
        if (blackDot == null)
        {
            blackDot = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            blackDot.transform.SetParent(transform);
            blackDot.transform.localScale = Vector3.one * 0.1f;
            blackDot.transform.localPosition = Vector3.up * 0.5f;  // Start at "north pole" for |0⟩
        }
        dotRenderer = blackDot.GetComponent<Renderer>();
        originalDotPosition = blackDot.transform.localPosition;
        
        // Create black material for dot
        Material blackMaterial = new Material(Shader.Find("Standard"));
        blackMaterial.color = Color.black;
        dotRenderer.material = blackMaterial;
        
        // Setup line renderer if present
        if (connectionLine != null)
        {
            connectionLine.enabled = false;
            connectionLine.startWidth = 0.02f;
            connectionLine.endWidth = 0.02f;
        }
        
        // Setup particle system
        if (superpositionEffect == null)
        {
            GameObject particleObject = new GameObject("SuperpositionEffect");
            particleObject.transform.SetParent(transform);
            particleObject.transform.localPosition = Vector3.zero;
            superpositionEffect = particleObject.AddComponent<ParticleSystem>();
            ConfigureSuperpositionEffect();
        }
        
        // Initially disable effects
        superpositionEffect.gameObject.SetActive(false);
    }
    
    void ConfigureSuperpositionEffect()
    {
        var main = superpositionEffect.main;
        main.startLifetime = 1f;
        main.startSpeed = 0.5f;
        main.maxParticles = 20;
        main.startSize = 0.05f;
        main.startColor = new Color(0.8f, 0.4f, 1f, 0.7f);  // Purple with transparency
        main.simulationSpace = ParticleSystemSimulationSpace.Local;
        
        var emission = superpositionEffect.emission;
        emission.rateOverTime = 10f;
        
        var shape = superpositionEffect.shape;
        shape.enabled = true;
        shape.shapeType = ParticleSystemShapeType.Sphere;
        shape.radius = 0.6f;
        
        var velocityOverLifetime = superpositionEffect.velocityOverLifetime;
        velocityOverLifetime.enabled = true;
        velocityOverLifetime.space = ParticleSystemSimulationSpace.Local;
        velocityOverLifetime.radial = new ParticleSystem.MinMaxCurve(0.2f);
        
        var colorOverLifetime = superpositionEffect.colorOverLifetime;
        colorOverLifetime.enabled = true;
        Gradient gradient = new Gradient();
        gradient.SetKeys(
            new GradientColorKey[] { new GradientColorKey(Color.white, 0.0f), new GradientColorKey(new Color(0.8f, 0.4f, 1f), 1.0f) },
            new GradientAlphaKey[] { new GradientAlphaKey(0.8f, 0.0f), new GradientAlphaKey(0.0f, 1.0f) }
        );
        colorOverLifetime.color = gradient;
    }
    
    /// <summary>
    /// Update the qubit visualization based on probability values
    /// </summary>
    /// <param name="probability0">Probability of being in |0⟩ state</param>
    /// <param name="probability1">Probability of being in |1⟩ state</param>
    /// <param name="entangled">Whether this qubit is entangled with others</param>
    public void UpdateVisualization(float probability0, float probability1, bool entangled = false)
    {
        prob0 = probability0;
        prob1 = probability1;
        isEntangled = entangled;
        
        // Determine if in superposition (neither probability is very close to 0 or 1)
        isInSuperposition = Mathf.Abs(prob0 - prob1) < 0.1f && prob0 > 0.1f && prob1 > 0.1f;
        
        // Stop current animation
        if (currentAnimation != null)
        {
            StopCoroutine(currentAnimation);
        }
        
        // Start appropriate animation
        if (isInSuperposition)
        {
            currentAnimation = StartCoroutine(AnimateSuperposition());
        }
        else
        {
            currentAnimation = StartCoroutine(AnimateDefiniteState());
        }
        
        // Update sphere material
        UpdateSphereMaterial();
    }
    
    void UpdateSphereMaterial()
    {
        if (sphereRenderer == null) return;
        
        if (isEntangled && entangledMaterial != null)
        {
            sphereRenderer.material = entangledMaterial;
        }
        else if (isInSuperposition && superpositionMaterial != null)
        {
            sphereRenderer.material = superpositionMaterial;
        }
        else if (prob0 > prob1 && state0Material != null)
        {
            sphereRenderer.material = state0Material;
        }
        else if (state1Material != null)
        {
            sphereRenderer.material = state1Material;
        }
    }
    
    IEnumerator AnimateSuperposition()
    {
        // Enable superposition effects
        superpositionEffect.gameObject.SetActive(true);
        superpositionEffect.Play();
        
        while (isInSuperposition)
        {
            // Animate black dot randomly on sphere surface
            float theta = Random.Range(0f, 2f * Mathf.PI);
            float phi = Random.Range(0f, Mathf.PI);
            
            Vector3 targetPosition = new Vector3(
                0.5f * Mathf.Sin(phi) * Mathf.Cos(theta),
                0.5f * Mathf.Cos(phi),
                0.5f * Mathf.Sin(phi) * Mathf.Sin(theta)
            );
            
            // Smoothly move dot to target position
            float moveTime = 0.1f;
            Vector3 startPosition = blackDot.transform.localPosition;
            float elapsedTime = 0f;
            
            while (elapsedTime < moveTime)
            {
                elapsedTime += Time.deltaTime;
                float t = elapsedTime / moveTime;
                blackDot.transform.localPosition = Vector3.Lerp(startPosition, targetPosition, t);
                yield return null;
            }
            
            // Pulse sphere
            float pulseScale = 1f + 0.1f * Mathf.Sin(Time.time * pulseSpeed);
            sphere.transform.localScale = originalSphereScale * pulseScale;
            
            // Rotate sphere
            sphere.transform.Rotate(Vector3.up, rotationSpeed * Time.deltaTime);
            
            yield return new WaitForSeconds(0.05f);
        }
        
        // Disable superposition effects
        superpositionEffect.Stop();
        superpositionEffect.gameObject.SetActive(false);
    }
    
    IEnumerator AnimateDefiniteState()
    {
        // Disable superposition effects
        superpositionEffect.Stop();
        superpositionEffect.gameObject.SetActive(false);
        
        // Position dot based on dominant state
        Vector3 targetPosition;
        if (prob0 > prob1)
        {
            // |0⟩ state - dot at "north pole"
            targetPosition = Vector3.up * 0.5f;
        }
        else
        {
            // |1⟩ state - dot at "south pole"
            targetPosition = Vector3.down * 0.5f;
        }
        
        // Smoothly move dot to target position
        float moveTime = 0.5f;
        Vector3 startPosition = blackDot.transform.localPosition;
        float elapsedTime = 0f;
        
        while (elapsedTime < moveTime)
        {
            elapsedTime += Time.deltaTime;
            float t = Mathf.SmoothStep(0f, 1f, elapsedTime / moveTime);
            blackDot.transform.localPosition = Vector3.Lerp(startPosition, targetPosition, t);
            
            // Gentle pulsing
            if (isEntangled)
            {
                float pulseScale = 1f + 0.05f * Mathf.Sin(Time.time * pulseSpeed);
                sphere.transform.localScale = originalSphereScale * pulseScale;
            }
            else
            {
                sphere.transform.localScale = originalSphereScale;
            }
            
            yield return null;
        }
        
        // Continue gentle animation if entangled
        while (isEntangled)
        {
            float pulseScale = 1f + 0.05f * Mathf.Sin(Time.time * pulseSpeed);
            sphere.transform.localScale = originalSphereScale * pulseScale;
            sphere.transform.Rotate(Vector3.up, rotationSpeed * 0.3f * Time.deltaTime);
            yield return null;
        }
        
        // Reset scale
        sphere.transform.localScale = originalSphereScale;
    }
    
    /// <summary>
    /// Create a visual connection to another qubit (for entanglement visualization)
    /// </summary>
    /// <param name="otherQubit">The other qubit to connect to</param>
    /// <param name="connectionStrength">Strength of the connection (0-1)</param>
    public void CreateConnectionTo(QubitVisualizer otherQubit, float connectionStrength = 1f)
    {
        if (connectionLine == null || otherQubit == null) return;
        
        connectionLine.enabled = true;
        connectionLine.positionCount = 2;
        connectionLine.SetPosition(0, transform.position);
        connectionLine.SetPosition(1, otherQubit.transform.position);
        
        // Set connection color based on strength
        Color connectionColor = Color.Lerp(Color.white, Color.yellow, connectionStrength);
        connectionColor.a = 0.7f;
        connectionLine.startColor = connectionColor;
        connectionLine.endColor = connectionColor;
        
        // Animate connection
        StartCoroutine(AnimateConnection(connectionStrength));
    }
    
    IEnumerator AnimateConnection(float strength)
    {
        while (connectionLine.enabled)
        {
            float pulse = Mathf.Sin(Time.time * pulseSpeed) * 0.5f + 0.5f;
            float width = 0.02f + (0.01f * pulse * strength);
            connectionLine.startWidth = width;
            connectionLine.endWidth = width;
            yield return null;
        }
    }
    
    /// <summary>
    /// Remove the connection line
    /// </summary>
    public void RemoveConnection()
    {
        if (connectionLine != null)
        {
            connectionLine.enabled = false;
        }
    }
    
    void OnDestroy()
    {
        if (currentAnimation != null)
        {
            StopCoroutine(currentAnimation);
        }
    }
}