# Railway Deployment Guide for CV Project

## Prerequisites
1. A Railway account (sign up at https://railway.app)
2. Git installed on your computer
3. Your Flask app code ready

## Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)
```bash
git init
git add .
git commit -m "Initial commit for Railway deployment"
```

### 1.2 Create a GitHub Repository
1. Go to GitHub.com and create a new repository
2. Push your code to GitHub:
```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Railway

### 2.1 Connect to Railway
1. Go to https://railway.app
2. Sign in with your GitHub account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository

### 2.2 Configure Environment Variables
In your Railway project dashboard, go to the "Variables" tab and add these environment variables:

```
FLASK_ENV=production
PORT=5000
```

### 2.3 Deploy
1. Railway will automatically detect your Python app
2. It will use the `requirements.txt` file to install dependencies
3. The `Procfile` will tell Railway how to start your app
4. Click "Deploy" and wait for the build to complete

## Step 3: Configure Custom Domain (Optional)

### 3.1 Add Custom Domain
1. In your Railway project, go to "Settings"
2. Click "Domains"
3. Add your custom domain
4. Update your DNS settings as instructed

## Step 4: Monitor Your Deployment

### 4.1 Check Logs
- Go to your Railway project dashboard
- Click on "Deployments" to see build logs
- Monitor the "Logs" tab for runtime logs

### 4.2 Health Checks
- Railway will automatically check your app's health
- Make sure your app responds to the root path `/`

## Step 5: Database Considerations

### 5.1 Current Setup
Your app currently uses SQLite databases stored locally:
- `users.db`
- `jobs.db`

### 5.2 For Production (Recommended)
Consider migrating to a proper database service:

#### Option A: Railway PostgreSQL
1. Add a PostgreSQL service in Railway
2. Update your app to use PostgreSQL instead of SQLite
3. Set database connection string as environment variable

#### Option B: External Database
- Use services like Supabase, PlanetScale, or AWS RDS
- Update connection strings in your app

## Troubleshooting

### Common Issues

#### 1. Build Failures
- Check that all dependencies are in `requirements.txt`
- Ensure Python version is compatible
- Check build logs for specific errors

#### 2. Runtime Errors
- Check application logs in Railway dashboard
- Ensure all environment variables are set
- Verify database connections

#### 3. Port Issues
- Railway automatically sets the `PORT` environment variable
- Your app should use `os.environ.get('PORT', 5000)`

#### 4. Externally-Managed-Environment Error
If you see this error during build:
```
error: externally-managed-environment
× This environment is externally managed
```

**Solution**: The configuration files have been updated to handle this. If the error persists:
1. Railway will automatically handle this with the current setup
2. The build process uses `--user` flag for pip installations
3. If issues continue, try removing `nixpacks.toml` and let Railway use default build

### Debug Commands
```bash
# Check if your app runs locally
python app.py

# Test with gunicorn locally
gunicorn app:app --bind 0.0.0.0:5000

# Check requirements installation
pip install -r requirements.txt
```

## File Structure for Railway
```
your-project/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Railway start command
├── railway.json          # Railway configuration
├── runtime.txt           # Python version
├── buildpacks.txt        # Buildpack specification
├── static/               # Static files
├── templates/            # HTML templates
└── README.md
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Port number for the app | 5000 |
| `FLASK_ENV` | Flask environment | production |
| `SECRET_KEY` | Flask secret key | (set in app.py) |

## Support
- Railway Documentation: https://docs.railway.app
- Flask Documentation: https://flask.palletsprojects.com
- Gunicorn Documentation: https://gunicorn.org

## Next Steps
1. Set up automatic deployments from GitHub
2. Configure monitoring and alerts
3. Set up a production database
4. Implement proper logging
5. Add SSL certificates (automatic with Railway) 