#!/bin/bash

echo "🚀 Railway Deployment Script for CV Project"
echo "=============================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
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
    git commit -m "Update for Railway deployment"
    git push origin main
    echo "✅ Code pushed to GitHub"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Go to https://railway.app"
echo "2. Sign in with your GitHub account"
echo "3. Click 'New Project'"
echo "4. Select 'Deploy from GitHub repo'"
echo "5. Choose your repository"
echo "6. Add environment variables:"
echo "   - FLASK_ENV=production"
echo "   - PORT=5000"
echo "7. Deploy!"
echo ""
echo "📖 For detailed instructions, see RAILWAY_DEPLOYMENT.md" 