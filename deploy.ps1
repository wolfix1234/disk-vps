# PowerShell script for Windows users
# Build and push Docker image script
# Usage: .\deploy.ps1 [tag] [registry]

param(
    [string]$Tag = "latest",
    [string]$Registry = "your-registry.com"  # Replace with your registry
)

# Configuration
$ImageName = "store-api"
$FullImageName = "$Registry/$ImageName`:$Tag"

Write-Host "🏗️  Building Docker image: $FullImageName" -ForegroundColor Green

# Build the image
docker build -t $FullImageName .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Build successful!" -ForegroundColor Green
    
    Write-Host "🚀 Pushing to registry..." -ForegroundColor Yellow
    docker push $FullImageName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Push successful!" -ForegroundColor Green
        Write-Host "📦 Image available at: $FullImageName" -ForegroundColor Cyan
        
        Write-Host ""
        Write-Host "🔧 To deploy to Kubernetes:" -ForegroundColor Yellow
        Write-Host "1. Update k8s-deployment.yaml with image: $FullImageName"
        Write-Host "2. Run: kubectl apply -f k8s-deployment.yaml"
        Write-Host "3. Run: kubectl apply -f k8s-ingress.yaml"
    } else {
        Write-Host "❌ Push failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}