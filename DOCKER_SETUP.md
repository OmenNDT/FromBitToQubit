# Quantum Visualizer 3D - Docker Setup Guide

## Overview

This guide provides comprehensive instructions for running the Quantum Visualizer 3D backend using Docker. We provide two versions:

1. **Simple Version**: Fast build, lightweight, demonstration purposes
2. **Full Version**: Complete Qiskit integration, production-ready

## Prerequisites

- Docker Engine 20.0+
- Docker Compose 2.0+
- 4GB+ available RAM
- Internet connection for downloading dependencies

## Quick Start

### Option 1: Simple Version (Recommended for Testing)

```bash
# Clone/navigate to project directory
cd quantum-visualizer-3d

# Build and run the simple version
docker-compose -f docker-compose.simple.yml up --build

# Access the API at http://localhost:5000
```

### Option 2: Full Version with Qiskit

```bash
# Build and run the full version
docker-compose up --build

# Access the API at http://localhost:5000
# Nginx proxy available at http://localhost:80 (production mode)
```

## Detailed Setup Instructions

### 1. Simple Version Deployment

The simple version is perfect for development and demonstration:

```bash
# Build the simple container
docker build -f Dockerfile.simple -t quantum-visualizer-simple .

# Run the container
docker run -d \
  --name quantum-backend-simple \
  -p 5000:5000 \
  --restart unless-stopped \
  quantum-visualizer-simple

# Check container status
docker ps
docker logs quantum-backend-simple
```

### 2. Full Version Deployment

The full version includes complete Qiskit integration:

```bash
# Build the full container (this may take 10-15 minutes)
docker build -t quantum-visualizer-full .

# Run with docker-compose (recommended)
docker-compose up -d

# Or run manually
docker run -d \
  --name quantum-backend-full \
  -p 5000:5000 \
  -v $(pwd)/circuits:/app/circuits:ro \
  --restart unless-stopped \
  quantum-visualizer-full
```

### 3. Production Deployment with Nginx

```bash
# Run with nginx proxy and production settings
docker-compose --profile production up -d

# This will start:
# - Quantum backend on internal network
# - Nginx proxy on port 80 with rate limiting and CORS
```

## Configuration Options

### Environment Variables

You can customize the deployment using environment variables:

```bash
# Create .env file
cat > .env << EOF
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
FLASK_ENV=production
EOF

# Use with docker-compose
docker-compose --env-file .env up -d
```

### Available Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Host to bind the Flask app |
| `FLASK_PORT` | `5000` | Port to run the Flask app |
| `FLASK_DEBUG` | `false` | Enable debug mode |
| `FLASK_ENV` | `production` | Flask environment |

## Testing the Deployment

### 1. Health Check

```bash
# Test if the service is running
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "message": "Quantum Visualizer 3D Backend is running",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "qiskit_available": true,
  "version": "1.0.0",
  "environment": "docker"
}
```

### 2. System Information

```bash
# Get system information
curl http://localhost:5000/info

# Check available examples
curl http://localhost:5000/example_circuits
```

### 3. Test Quantum Simulation

```bash
# Test Bell state simulation
curl -X POST http://localhost:5000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "qiskit_code": "circ = QuantumCircuit(2)\ncirc.h(0)\ncirc.cx(0, 1)"
  }'
```

### 4. Automated Testing

```bash
# Run the test script against Docker container
python test_simple_backend.py

# Or create a test container
docker run --rm --network host \
  -v $(pwd)/test_simple_backend.py:/test.py \
  python:3.11-slim python /test.py
```

## Container Management

### Viewing Logs

```bash
# View real-time logs
docker-compose logs -f quantum-backend

# View specific container logs
docker logs quantum-visualizer-backend

# View last 100 lines
docker logs --tail 100 quantum-visualizer-backend
```

### Container Health Monitoring

```bash
# Check container health
docker inspect quantum-visualizer-backend | grep -A 10 "Health"

# Manual health check
docker exec quantum-visualizer-backend curl -f http://localhost:5000/health
```

### Scaling and Updates

```bash
# Update the container
docker-compose pull
docker-compose up -d

# Scale horizontally (multiple instances)
docker-compose up -d --scale quantum-backend=3

# Rolling update
docker-compose up -d --no-deps --build quantum-backend
```

## Networking

### Docker Network Configuration

The containers use a custom bridge network for isolation:

```yaml
networks:
  quantum-network:
    driver: bridge
```

### Port Mappings

- **5000**: Flask application (simple version)
- **80**: Nginx proxy (full version with production profile)
- **443**: HTTPS (when SSL certificates are configured)

### Unity Integration

Configure Unity to connect to the Docker container:

```csharp
// In QuantumSimulationManager.cs
public string backendUrl = "http://localhost:5000";  // For local Docker
// OR
public string backendUrl = "http://your-server-ip:5000";  // For remote Docker
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Use different port
docker run -p 5001:5000 quantum-visualizer-simple
```

#### 2. Build Failures
```bash
# Clean build without cache
docker build --no-cache -f Dockerfile.simple -t quantum-visualizer-simple .

# Check Docker system resources
docker system df
docker system prune  # Clean up if needed
```

#### 3. Memory Issues
```bash
# Monitor container resource usage
docker stats quantum-visualizer-backend

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > Increase to 4GB+
```

#### 4. CORS Issues
```bash
# Check if CORS headers are present
curl -I -X OPTIONS http://localhost:5000/simulate \
  -H "Origin: http://localhost:3000"

# Add custom CORS origin in nginx.conf if needed
```

### Debug Mode

Run containers in debug mode for development:

```bash
# Simple version with debug
docker run -it --rm \
  -p 5000:5000 \
  -e FLASK_DEBUG=true \
  quantum-visualizer-simple

# Full version with debug
docker-compose -f docker-compose.yml \
  -f docker-compose.debug.yml up
```

## Performance Optimization

### 1. Multi-stage Builds

The Dockerfiles use multi-stage builds to minimize image size:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
# ... build dependencies

# Runtime stage  
FROM python:3.11-slim as runtime
COPY --from=builder /app /app
```

### 2. Layer Caching

Optimize build times by ordering layers correctly:

1. System dependencies (changes rarely)
2. Python requirements (changes occasionally)
3. Application code (changes frequently)

### 3. Resource Limits

Set appropriate resource limits:

```yaml
services:
  quantum-backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

## Security Considerations

### 1. Non-root User

Both Dockerfiles create and use a non-root user:

```dockerfile
RUN useradd --create-home --shell /bin/bash quantum
USER quantum
```

### 2. Minimal Base Images

Using `python:3.11-slim` instead of full Ubuntu reduces attack surface.

### 3. Network Security

- Custom bridge network isolates containers
- Nginx proxy provides rate limiting
- CORS configuration restricts origins

### 4. Secrets Management

For production, use Docker secrets:

```yaml
services:
  quantum-backend:
    secrets:
      - api_key
secrets:
  api_key:
    file: ./secrets/api_key.txt
```

## Monitoring and Logging

### 1. Health Checks

Built-in health checks ensure container reliability:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1
```

### 2. Structured Logging

The application uses structured logging:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 3. Log Management

```bash
# Configure log rotation
docker run --log-driver=json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  quantum-visualizer-simple
```

## Deployment Strategies

### 1. Development

```bash
# Local development with hot reload
docker-compose -f docker-compose.dev.yml up
```

### 2. Staging

```bash
# Staging environment
docker-compose -f docker-compose.staging.yml up -d
```

### 3. Production

```bash
# Production with nginx, monitoring, and logging
docker-compose --profile production up -d
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t quantum-visualizer .
      - name: Run tests
        run: docker run --rm quantum-visualizer python test_simple_backend.py
      - name: Deploy to production
        run: docker-compose --profile production up -d
```

## Backup and Recovery

### 1. Data Backup

```bash
# Backup container volumes
docker run --rm -v quantum-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/quantum-backup.tar.gz /data
```

### 2. Configuration Backup

```bash
# Backup docker-compose and configs
tar czf quantum-config-backup.tar.gz \
  docker-compose*.yml nginx.conf Dockerfile*
```

## Support and Updates

### 1. Version Updates

```bash
# Update to latest version
git pull origin main
docker-compose up -d --build
```

### 2. Rollback

```bash
# Rollback to previous version
docker-compose down
git checkout previous-tag
docker-compose up -d --build
```

## Conclusion

The Docker setup provides a robust, scalable, and secure deployment option for the Quantum Visualizer 3D backend. The simple version is perfect for development and testing, while the full version with nginx is production-ready.

For additional support or custom deployments, refer to the main project documentation or create an issue in the project repository.