# Docker Deployment Guide for CV Project

## 🐳 Docker Setup for Railway Deployment

This guide will help you deploy your Flask app to Railway using Docker for better reliability and consistency.

## Prerequisites

1. **Docker installed** (for local testing)
2. **Railway account** (https://railway.app)
3. **Git repository** with your code

## 🚀 Quick Deployment Steps

### Step 1: Test Locally with Docker

```bash
# Build the Docker image
docker build -t cv-project .

# Run the container locally
docker run -p 5000:5000 cv-project

# Or use docker-compose
docker-compose up --build
```

### Step 2: Deploy to Railway

1. **Push your code to GitHub:**
```bash
git add .
git commit -m "Add Docker configuration for Railway deployment"
git push origin main
```

2. **Deploy on Railway:**
   - Go to https://railway.app
   - Sign in with GitHub
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will automatically detect the Dockerfile

3. **Configure Environment Variables:**
   - Go to your project's "Variables" tab
   - Add: `FLASK_ENV=production`

## 🔧 Docker Configuration Explained

### Dockerfile Features:
- **Python 3.9 slim image** - Lightweight and secure
- **System dependencies** - All required libraries for PDF processing
- **Startup script** - Handles database initialization safely
- **Health checks** - Automatic monitoring via `/health` endpoint
- **Security** - Non-root user and minimal attack surface

### Key Benefits:
- ✅ **Consistent environment** - Same setup everywhere
- ✅ **No dependency conflicts** - Isolated environment
- ✅ **Safe database initialization** - Prevents worker conflicts
- ✅ **Easy scaling** - Railway can handle multiple instances
- ✅ **Better debugging** - Local Docker matches production

## 🐛 Troubleshooting

### Common Issues:

#### 1. Database Initialization Errors
**Problem**: `sqlite3.OperationalError: table USERS already exists`

**Solution**: The startup script (`start.sh`) now handles database initialization safely:
- Creates databases before starting Gunicorn
- Uses `CREATE TABLE IF NOT EXISTS` to prevent conflicts
- Single worker initially to avoid race conditions

#### 2. Build Failures
```bash
# Check Docker build locally
docker build -t cv-project . --no-cache

# Check logs
docker logs <container_id>
```

#### 3. Port Issues
- Railway automatically sets `PORT` environment variable
- Dockerfile exposes port 5000
- Gunicorn binds to `0.0.0.0:5000`

#### 4. Health Check Failures
- Health check uses `/health` endpoint
- 60-second start period allows for database initialization
- Check logs if health checks fail

### Debug Commands:

```bash
# Test locally
docker-compose up --build

# Check container logs
docker logs <container_id>

# Enter container for debugging
docker exec -it <container_id> /bin/bash

# Check if app is running
curl http://localhost:5000/health
```

## 📁 File Structure

```
your-project/
├── Dockerfile              # Docker configuration
├── start.sh               # Startup script with DB init
├── docker-compose.yml      # Local development
├── .dockerignore          # Exclude files from build
├── railway.json           # Railway configuration
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/                # Static files
├── templates/             # HTML templates
└── README.md
```

## 🔄 Deployment Workflow

1. **Local Development:**
   ```bash
   docker-compose up --build
   ```

2. **Test Changes:**
   - Make changes to your code
   - Test locally with Docker
   - Ensure everything works

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

4. **Monitor:**
   - Check Railway dashboard
   - Monitor logs
   - Verify health checks

## 🚀 Advanced Configuration

### Custom Domain:
1. Go to Railway project settings
2. Add custom domain
3. Update DNS settings

### Environment Variables:
```bash
FLASK_ENV=production
PORT=5000
SECRET_KEY=your-secret-key
```

### Scaling:
- Railway automatically scales based on traffic
- Docker containers can be easily replicated
- Load balancing is handled automatically

## 📊 Monitoring

### Health Checks:
- Automatic health checks every 30 seconds
- Uses `/health` endpoint for monitoring
- 60-second start period for database initialization
- Railway will restart unhealthy containers

### Logs:
- Access logs in Railway dashboard
- Real-time log streaming
- Error tracking and debugging

## 🔒 Security

### Docker Security:
- Non-root user execution
- Minimal base image
- Regular security updates
- Isolated container environment

### Best Practices:
- Keep dependencies updated
- Use environment variables for secrets
- Regular security scans
- Monitor for vulnerabilities

## 🆘 Support

### Resources:
- [Railway Documentation](https://docs.railway.app)
- [Docker Documentation](https://docs.docker.com)
- [Flask Documentation](https://flask.palletsprojects.com)

### Common Commands:
```bash
# Build and run
docker build -t cv-project . && docker run -p 5000:5000 cv-project

# View logs
docker logs <container_id>

# Stop container
docker stop <container_id>

# Remove container
docker rm <container_id>
```

## ✅ Success Checklist

- [ ] Docker builds successfully locally
- [ ] App runs in Docker container
- [ ] Database initialization works without conflicts
- [ ] Health check endpoint responds correctly
- [ ] All features work in Docker
- [ ] Code pushed to GitHub
- [ ] Railway deployment successful
- [ ] Health checks passing
- [ ] Custom domain configured (optional)
- [ ] Environment variables set
- [ ] Monitoring configured

Your Flask app is now ready for reliable Docker deployment on Railway! 🎉 