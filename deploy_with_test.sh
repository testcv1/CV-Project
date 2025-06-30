#!/bin/bash

echo "🐳 Docker Railway Deployment with Testing"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is installed"

# Test the app locally first
echo "🧪 Testing app locally..."
if python3 test_app.py; then
    echo "✅ Local tests passed"
else
    echo "❌ Local tests failed. Please fix the issues before deploying."
    exit 1
fi

# Test Docker build locally
echo "🔨 Testing Docker build locally..."
if docker build -t cv-project .; then
    echo "✅ Docker build successful"
else
    echo "❌ Docker build failed. Please check the errors above."
    exit 1
fi

# Test Docker run locally
echo "🚀 Testing Docker run locally..."
docker run -d --name cv-test -p 5000:5000 cv-project
sleep 10

# Test health endpoint
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Docker container health check passed"
    docker stop cv-test
    docker rm cv-test
else
    echo "❌ Docker container health check failed"
    echo "Container logs:"
    docker logs cv-test
    docker stop cv-test
    docker rm cv-test
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit with Docker configuration and testing"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if remote origin exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "⚠️  No remote origin found!"
    echo "Please create a GitHub repository and run:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"
    echo "git branch -M main"
    echo "git push -u origin main"
else
    echo "✅ Remote origin found"
    echo "🔄 Pushing to GitHub..."
    git add .
    git commit -m "Add Docker configuration with testing for Railway deployment"
    git push origin main
    echo "✅ Code pushed to GitHub"
fi

echo ""
echo "🎯 Next Steps for Railway Deployment:"
echo "1. Go to https://railway.app"
echo "2. Sign in with your GitHub account"
echo "3. Click 'New Project'"
echo "4. Select 'Deploy from GitHub repo'"
echo "5. Choose your repository"
echo "6. Railway will automatically detect the Dockerfile"
echo "7. Add environment variables:"
echo "   - FLASK_ENV=production"
echo "8. Deploy!"
echo ""
echo "📖 For detailed instructions, see DOCKER_DEPLOYMENT.md"
echo ""
echo "🧪 To test locally:"
echo "docker-compose up --build" 