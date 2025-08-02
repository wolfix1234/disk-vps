#!/bin/bash

# Build and push Docker image script
# Usage: ./build-and-push.sh [tag] [registry]

# Configuration
IMAGE_NAME="store-api"
TAG=${1:-latest}
REGISTRY=${2:-"your-registry.com"}  # Replace with your registry
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "🏗️  Building Docker image: ${FULL_IMAGE_NAME}"

# Build the image
docker build -t ${FULL_IMAGE_NAME} .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    echo "🚀 Pushing to registry..."
    docker push ${FULL_IMAGE_NAME}
    
    if [ $? -eq 0 ]; then
        echo "✅ Push successful!"
        echo "📦 Image available at: ${FULL_IMAGE_NAME}"
        
        echo ""
        echo "🔧 To deploy to Kubernetes:"
        echo "1. Update k8s-deployment.yaml with image: ${FULL_IMAGE_NAME}"
        echo "2. Run: kubectl apply -f k8s-deployment.yaml"
        echo "3. Run: kubectl apply -f k8s-ingress.yaml"
    else
        echo "❌ Push failed!"
        exit 1
    fi
else
    echo "❌ Build failed!"
    exit 1
fi