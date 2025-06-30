#!/bin/bash

echo "🐳 Docker Railway Deployment Script for CV Project"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "✅ Docker is installed"

# Test Docker build locally
echo "🔨 Testing Docker build locally..."
if docker build -t cv-project .; then
    echo "✅ Docker build successful"
else
    echo "❌ Docker build failed. Please check the errors above."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit with Docker configuration"
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
    git commit -m "Add Docker configuration for Railway deployment"
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