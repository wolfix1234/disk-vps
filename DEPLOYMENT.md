# Store API Deployment Guide

This guide explains how to containerize and deploy the Store Management API to a Kubernetes cluster.

## 🐳 Docker Deployment

### Prerequisites
- Docker installed
- Docker registry access (Docker Hub, AWS ECR, Google Container Registry, etc.)

### Local Testing with Docker Compose

1. **Test locally first:**
   ```bash
   docker-compose up --build
   ```
   
2. **Access the API:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Building and Pushing to Registry

1. **Update registry information:**
   - Edit `build-and-push.sh` (Linux/Mac) or `deploy.ps1` (Windows)
   - Replace `your-registry.com` with your actual registry

2. **Build and push:**
   ```bash
   # Linux/Mac
   ./build-and-push.sh v1.0.0 your-registry.com
   
   # Windows PowerShell
   .\deploy.ps1 -Tag "v1.0.0" -Registry "your-registry.com"
   ```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster access
- kubectl configured
- Ingress controller (nginx-ingress recommended)
- Persistent storage provisioner

### Deployment Steps

1. **Update configuration files:**
   
   **k8s-deployment.yaml:**
   ```yaml
   # Update the image reference
   image: your-registry.com/store-api:v1.0.0
   
   # Update API token secret (base64 encoded)
   api-token: <your-base64-encoded-token>
   ```
   
   **k8s-ingress.yaml:**
   ```yaml
   # Update domain name
   - host: your-domain.com
   ```

2. **Deploy to cluster:**
   ```bash
   # Apply deployment and services
   kubectl apply -f k8s-deployment.yaml
   
   # Apply ingress
   kubectl apply -f k8s-ingress.yaml
   ```

3. **Verify deployment:**
   ```bash
   # Check pods
   kubectl get pods -l app=store-api
   
   # Check services
   kubectl get svc store-api-service
   
   # Check ingress
   kubectl get ingress store-api-ingress
   
   # View logs
   kubectl logs -l app=store-api -f
   ```

### Configuration Options

#### Environment Variables
- `ENVIRONMENT`: Set to "production"
- `API_TOKEN`: Your API authentication token
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

#### Resource Limits
Current settings in `k8s-deployment.yaml`:
- **Requests:** 256Mi RAM, 250m CPU
- **Limits:** 512Mi RAM, 500m CPU

Adjust based on your needs and cluster capacity.

#### Storage
- **Uploads:** 10Gi persistent volume for file uploads
- **Logs:** 5Gi persistent volume for application logs

## 🔧 Production Features Enabled

The containerized version includes all production features:

- ✅ **Security Headers:** CSP, XSS protection, frame options
- ✅ **Rate Limiting:** 100 requests per minute per IP
- ✅ **Request Logging:** All requests logged with timing
- ✅ **CORS:** Configurable cross-origin policies
- ✅ **Health Checks:** Kubernetes liveness/readiness probes
- ✅ **Error Handling:** Comprehensive exception handling

## 🔍 Monitoring and Troubleshooting

### Health Checks
- **Endpoint:** `/health`
- **Kubernetes:** Automatic liveness and readiness probes
- **Docker:** Built-in health check

### Logs
```bash
# Kubernetes logs
kubectl logs -l app=store-api -f

# Docker logs
docker logs store-api-container -f
```

### Common Issues

1. **Pod not starting:**
   - Check image pull secrets
   - Verify resource limits
   - Check persistent volume claims

2. **502/503 errors:**
   - Verify service endpoints
   - Check pod health status
   - Review application logs

3. **File upload issues:**
   - Ensure persistent volumes are mounted
   - Check volume permissions
   - Verify storage class

## 🚀 Scaling

### Horizontal Scaling
```bash
# Scale to 5 replicas
kubectl scale deployment store-api --replicas=5
```

### Vertical Scaling
Update resource limits in `k8s-deployment.yaml` and reapply.

## 🔐 Security Considerations

1. **API Token:** Store in Kubernetes secrets, not in plain text
2. **TLS:** Use cert-manager for automatic SSL certificates
3. **Network Policies:** Restrict pod-to-pod communication
4. **Image Security:** Scan images for vulnerabilities
5. **RBAC:** Use least-privilege service accounts

## 📊 Performance Tuning

### Gunicorn Workers
Current: 4 workers. Adjust based on:
- CPU cores available
- Memory constraints
- Request patterns

### Database Connections
If using a database, configure connection pooling appropriately.

### Caching
Consider adding Redis for caching if needed.

## 🔄 Updates and Rollbacks

### Rolling Updates
```bash
# Update image
kubectl set image deployment/store-api store-api=your-registry.com/store-api:v1.1.0

# Check rollout status
kubectl rollout status deployment/store-api
```

### Rollbacks
```bash
# Rollback to previous version
kubectl rollout undo deployment/store-api

# Rollback to specific revision
kubectl rollout undo deployment/store-api --to-revision=2
```

## 📝 Next Steps

1. Set up monitoring (Prometheus + Grafana)
2. Configure log aggregation (ELK stack)
3. Implement CI/CD pipeline
4. Set up backup strategies for persistent data
5. Configure alerting for critical issues