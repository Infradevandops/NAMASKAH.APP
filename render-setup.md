# 🎨 Render Deployment Guide

## Quick Setup

### 1. Create render.yaml
```yaml
services:
  - type: web
    name: namaskah
    env: python
    buildCommand: "pip install -r requirements.txt && cd frontend && npm install && npm run build"
    startCommand: "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"
    healthCheckPath: "/health"
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: namaskah-db
          property: connectionString
      - key: SENTRY_DSN
        value: "https://2ce37686e54217bc6539cce15a0b3a3b@o4510054773555200.ingest.de.sentry.io/4510054775717968"

databases:
  - name: namaskah-db
    databaseName: namaskah
    user: Namaskah.App_user

static:
  - type: static
    name: namaskah-frontend
    staticPublishPath: ./frontend/build
    buildCommand: "cd frontend && npm install && npm run build"
    routes:
      - src: "/*"
        dest: "/index.html"
```

### 2. Deploy Steps
1. Connect GitHub repo to Render
2. Select "Web Service"
3. Use existing render.yaml
4. Deploy automatically

### 3. Custom Domain (Optional)
- Add your domain in Render dashboard
- Update DNS records
- SSL automatically handled