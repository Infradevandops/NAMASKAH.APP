# 🚀 namaskah Deployment Guide

## 🎯 **Deployment Overview**

namaskah supports multiple deployment strategies from local development to enterprise-scale production. This guide covers all deployment options with step-by-step instructions.

## 🐳 **Docker Quick Start (Recommended)**

```bash
# Clone and start with Docker
git clone <repository-url>
cd namaskah
./docker-dev.sh dev
```

## 🌐 **Render Deployment (Production)**

**Environment Variables for Render:**
```
JWT_SECRET_KEY = Namaskah.App2024SecureJWTKeyForProductionUse32Chars
PORT = 10000
DEBUG = false
TEXTVERIFIED_API_KEY = your_textverified_api_key_here
TWILIO_ACCOUNT_SID = your_twilio_account_sid_here
GROQ_API_KEY = your_groq_api_key_here
```

**Setup Steps:**
1. Create Web Service on Render
2. Connect GitHub repo: `https://github.com/Infradevandops/namaskah`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host=0.0.0.0 --port=10000`
5. Add environment variables above
6. Deploy!

---

## 🏠 **Local Development Deployment**

### **Quick Start**
```bash
# Clone and setup
git clone <repository-url>
cd namaskah
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start development server
uvicorn main:app --reload --port 8000
```

### **With Docker (Recommended)**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL=sqlite:///./namaskah.db

# Security
JWT_SECRET_KEY=your-secret-key-here

# Optional API Keys (use mocks if not provided)
TEXTVERIFIED_API_KEY=your-textverified-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
GROQ_API_KEY=your-groq-key
```

---

## ☁️ **Cloud Deployment Options**

### **Option 1: Railway (Recommended)**

**Why Railway?**
- Zero-config PostgreSQL
- Automatic HTTPS
- Git-based deployments
- Built-in monitoring

**Deployment Steps:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up

# Set environment variables
railway variables set JWT_SECRET_KEY=$(openssl rand -base64 32)
railway variables set TEXTVERIFIED_API_KEY=your-key
```

**Railway Configuration:**
```yaml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"
```

### **Option 2: Render**

**Why Render?**
- Free tier available
- Automatic SSL
- Easy database setup
- Built-in monitoring

**Deployment Steps:**
1. **Connect Repository**: Link your GitHub repository to Render
2. **Create Web Service**: 
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Add PostgreSQL**: Create PostgreSQL database service
4. **Set Environment Variables**: Add all required variables in Render dashboard

**Render Configuration:**
```yaml
# render.yaml
services:
  - type: web
    name: namaskah
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    
  - type: pserv
    name: namaskah-db
    env: postgresql
    plan: starter
```

### **Option 3: Heroku**

**Deployment Steps:**
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set JWT_SECRET_KEY=$(openssl rand -base64 32)
heroku config:set TEXTVERIFIED_API_KEY=your-key

# Deploy
git push heroku main
```

**Heroku Configuration:**
```
# Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
release: alembic upgrade head
```

### **Option 4: DigitalOcean App Platform**

**Deployment Steps:**
1. **Create App**: Connect GitHub repository
2. **Configure Build**: 
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Add Database**: Create managed PostgreSQL database
4. **Set Environment Variables**: Configure in App Platform dashboard

---

## 🐳 **Docker Production Deployment**

### **Production Docker Setup**
```bash
# Build production image
docker build -t namaskah:latest .

# Run with production config
docker run -d \
  --name namaskah \
  -p 80:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e JWT_SECRET_KEY=your-secret-key \
  namaskah:latest
```

### **Docker Compose Production**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "80:8000"
    environment:
      - DATABASE_URL=postgresql://namaskah:password@db:5432/namaskah
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=namaskah
      - POSTGRES_USER=namaskah
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

### **Kubernetes Deployment**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: namaskah
spec:
  replicas: 3
  selector:
    matchLabels:
      app: namaskah
  template:
    metadata:
      labels:
        app: namaskah
    spec:
      containers:
      - name: namaskah
        image: namaskah:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: namaskah-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: namaskah-secrets
              key: jwt-secret
```

---

## 🔧 **Production Configuration**

### **Environment Variables**
```env
# Production Environment (.env.production)

# Application
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/namaskah

# Security
JWT_SECRET_KEY=your-very-secure-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# External APIs
TEXTVERIFIED_API_KEY=your-textverified-api-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
GROQ_API_KEY=your-groq-api-key

# Performance
REDIS_URL=redis://localhost:6379
MAX_CONNECTIONS=100
POOL_SIZE=20
```

### **Database Setup**
```bash
# Initialize production database
alembic upgrade head

# Create admin user (optional)
python -c "
from models.user import User
from core.database import SessionLocal
from auth.utils import get_password_hash

db = SessionLocal()
admin = User(
    email='admin@yourdomain.com',
    username='admin',
    hashed_password=get_password_hash('secure-password'),
    is_admin=True
)
db.add(admin)
db.commit()
"
```

### **SSL/HTTPS Configuration**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://app:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📊 **Monitoring & Health Checks**

### **Health Check Endpoints**
- **Basic Health**: `GET /health`
- **Detailed Status**: `GET /health/detailed`
- **Database Check**: `GET /health/db`
- **External APIs**: `GET /health/apis`

### **Monitoring Setup**
```bash
# Check application health
curl https://yourdomain.com/health

# Monitor logs
docker-compose logs -f app

# Database monitoring
docker-compose exec db psql -U namaskah -c "SELECT * FROM pg_stat_activity;"
```

### **Performance Monitoring**
```python
# Add to your monitoring system
import requests
import time

def monitor_api_performance():
    start_time = time.time()
    response = requests.get('https://yourdomain.com/health')
    response_time = time.time() - start_time
    
    if response.status_code == 200 and response_time < 0.5:
        print("✅ API healthy")
    else:
        print("❌ API issues detected")
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

**Database Connection Issues:**
```bash
# Check database connectivity
docker-compose exec app python -c "
from core.database import engine
try:
    engine.connect()
    print('✅ Database connected')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

**API Key Issues:**
```bash
# Test API integrations
curl -X POST https://yourdomain.com/api/test/textverified
curl -X POST https://yourdomain.com/api/test/groq
```

**Performance Issues:**
```bash
# Check resource usage
docker stats

# Monitor database queries
docker-compose exec db psql -U namaskah -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"
```

### **Rollback Procedures**
```bash
# Rollback to previous version
docker-compose down
docker pull namaskah:previous-version
docker-compose up -d

# Database rollback
alembic downgrade -1
```

---

## 🔒 **Security Checklist**

### **Pre-Deployment Security**
- [ ] Generate strong JWT secret key
- [ ] Set secure database passwords
- [ ] Configure CORS origins for production domain
- [ ] Enable HTTPS/TLS certificates
- [ ] Set `DEBUG=false` in production
- [ ] Configure rate limiting
- [ ] Set up security headers (HSTS, CSP, etc.)

### **Post-Deployment Security**
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Set up intrusion detection
- [ ] Regular backup verification
- [ ] Security audit schedule

---

## 🎯 **Success Metrics**

### **Deployment Success Indicators**
- ✅ Health checks passing (200 OK)
- ✅ Database connectivity confirmed
- ✅ API endpoints responding <200ms
- ✅ WebSocket connections stable
- ✅ External API integrations working
- ✅ SSL certificates valid
- ✅ Monitoring alerts configured

### **Performance Targets**
- **API Response Time**: <100ms average
- **Uptime**: >99.9% availability
- **Error Rate**: <0.1% of requests
- **Database Queries**: <50ms average
- **Memory Usage**: <512MB per container

---

**🚀 Your namaskah platform is now ready for production deployment!**

Choose your preferred deployment method and follow the step-by-step instructions above. For additional support, check the troubleshooting section or create an issue in the repository.

---

**Last Updated**: December 2024  
**Deployment Status**: Production Ready ✅