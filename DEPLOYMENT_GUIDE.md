# 🚀 Namaskah.App Enterprise - Production Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying the Namaskah.App enterprise communication platform to production environments. The platform includes multi-tenant architecture, RBAC, voice/video calling, and AI-powered features.

## 🏗️ Architecture Overview

### **Infrastructure Components**
- **Backend**: FastAPI (Python 3.11) with PostgreSQL and Redis
- **Frontend**: React with TypeScript and Chart.js
- **Database**: PostgreSQL with enterprise schemas
- **Cache**: Redis for sessions and performance
- **Monitoring**: Sentry for error tracking and performance monitoring
- **Deployment**: Render (recommended) or Railway/AWS

### **Enterprise Features**
- ✅ Multi-Tenant Architecture with data isolation
- ✅ Role-Based Access Control (RBAC)
- ✅ WebRTC Voice & Video Calling
- ✅ AI-Powered Smart Routing
- ✅ Real-time Analytics Dashboard

## 🚀 Quick Start Deployment

### **Option 1: Render (Recommended)**

1. **Fork/Clone the Repository**
   ```bash
   git clone https://github.com/your-org/namaskah-app.git
   cd namaskah-app
   ```

2. **Set up Render Account**
   - Go to [render.com](https://render.com) and create an account
   - Connect your GitHub repository

3. **Deploy using Blueprint**
   - Use the `config/render.yaml` blueprint file
   - Render will automatically create all services

4. **Configure Environment Variables**
   ```bash
   # Required Secrets (set in Render dashboard)
   SECRET_KEY=your-32-char-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
   TEXTVERIFIED_API_KEY=your-textverified-key
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   GROQ_API_KEY=your-groq-api-key
   ```

### **Option 2: Railway**

1. **Deploy to Railway**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login and deploy
   railway login
   railway deploy
   ```

2. **Configure Environment Variables**
   - Use Railway dashboard to set environment variables
   - Database and Redis are auto-provisioned

## ⚙️ Environment Configuration

### **Required Environment Variables**

```bash
# Core Application
ENVIRONMENT=production
DEBUG=false
APP_VERSION=2.0.0
SECRET_KEY=your-32-character-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://host:6379/0

# External APIs
TEXTVERIFIED_API_KEY=your-api-key
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
GROQ_API_KEY=your-api-key

# Monitoring
SENTRY_DSN=https://your-dsn@sentry.io/project
SENTRY_ENVIRONMENT=production
ENABLE_PERFORMANCE_MONITORING=true

# Security
CORS_ORIGINS=["https://namaskah.app", "https://www.namaskah.app"]
ALLOWED_HOSTS=["your-app.render.com", "namaskah.app"]
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Health Checks
HEALTH_CHECK_ENABLED=true
LOG_LEVEL=INFO
```

### **Optional Environment Variables**

```bash
# Backup Configuration
BACKUP_ENABLED=false
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30

# Performance Tuning
PERFORMANCE_SAMPLE_RATE=0.1
RATE_LIMIT_BURST=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

## 🗄️ Database Setup

### **PostgreSQL Configuration**

The application uses PostgreSQL with the following enterprise schemas:

- **Core Schema**: Users, conversations, billing
- **Tenant Schema**: Multi-tenant data isolation
- **RBAC Schema**: Roles, permissions, user assignments
- **Call Schema**: WebRTC sessions, call history
- **AI Schema**: Routing rules, conversation intelligence

### **Database Migration**

```bash
# Run migrations during deployment
python -m alembic upgrade head

# Or use the deployment script
python scripts/setup_production_deployment.py
```

### **Database Backup Strategy**

```bash
# Automated backups (configure in your cloud provider)
# - Daily full backups
# - Hourly incremental backups
# - 30-day retention policy
# - Encrypted storage
```

## 🔧 Redis Configuration

### **Redis Usage**
- **Session Storage**: User sessions and authentication
- **Cache Layer**: API response caching
- **Real-time Features**: WebSocket connection management
- **Rate Limiting**: Request throttling
- **Background Jobs**: Task queuing

### **Redis Cluster Setup**
```yaml
# For production clusters
redis:
  cluster: true
  nodes:
    - host: redis-1:6379
    - host: redis-2:6379
    - host: redis-3:6379
  max_connections: 20
```

## 📊 Monitoring & Observability

### **Sentry Configuration**

```python
# Automatically configured via environment variables
# Error tracking, performance monitoring, release tracking
```

### **Health Checks**

The application provides comprehensive health checks:

- **`/health`**: Overall system health
- **`/health/db`**: Database connectivity
- **`/health/redis`**: Redis connectivity
- **`/health/external`**: External API connectivity

### **Metrics Collection**

```json
{
  "api_requests": true,
  "database_connections": true,
  "redis_operations": true,
  "tenant_activity": true,
  "verification_success": true,
  "call_quality": true,
  "ai_routing_performance": true
}
```

### **Logging Configuration**

```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/namaskah/app.log"
  max_bytes: 10MB
  backup_count: 5
```

## 🔒 Security Configuration

### **SSL/TLS**
- ✅ SSL redirect enabled
- ✅ Secure cookies configured
- ✅ HTTPS enforced

### **CORS Configuration**
```json
{
  "origins": ["https://namaskah.app", "https://www.namaskah.app"],
  "allow_credentials": true,
  "allow_methods": ["GET", "POST", "PUT", "DELETE"],
  "allow_headers": ["*"]
}
```

### **Rate Limiting**
```yaml
rate_limiting:
  enabled: true
  requests_per_minute: 100
  burst: 20
  strategy: "sliding_window"
```

## 🚀 Deployment Scripts

### **Production Deployment Setup**

```bash
# Run the comprehensive deployment setup
python scripts/setup_production_deployment.py

# This script performs:
# - Environment validation
# - Database setup and migrations
# - Redis configuration
# - Monitoring setup (Sentry, logging)
# - Security configuration
# - Performance optimization
# - Deployment validation
```

### **Monitoring Setup**

```bash
# Configure monitoring stack
python scripts/setup_monitoring.py

# Creates:
# - Sentry integration
# - Performance monitoring
# - Health checks
# - Metrics collection
# - Logging configuration
```

## 🧪 Testing & Validation

### **Pre-deployment Testing**

```bash
# Run full test suite
python -m pytest --cov=. --cov-report=term-missing

# Run enterprise feature tests
python -m pytest test_enterprise_features.py -v

# Run integration tests
python -c "
from main import app
from fastapi.testclient import TestClient
client = TestClient(app)
# Test endpoints...
"
```

### **Post-deployment Validation**

```bash
# Health checks
curl https://your-app.com/health

# API validation
curl https://your-app.com/docs

# Enterprise features
curl https://your-app.com/api/tenants
curl https://your-app.com/api/rbac/roles
```

## 📈 Performance Optimization

### **Database Optimization**
- Connection pooling configured
- Query optimization with indexes
- Read replicas for analytics queries

### **Caching Strategy**
- Redis caching for frequent queries
- CDN for static assets
- Browser caching headers

### **Scaling Considerations**
- Horizontal scaling with load balancer
- Database read replicas
- Redis cluster for high availability

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow**

The repository includes a comprehensive CI/CD pipeline (`.github/workflows/ci-cd.yml`) that:

- ✅ Runs backend and frontend tests
- ✅ Performs security scanning
- ✅ Executes integration tests
- ✅ Runs performance tests
- ✅ Deploys to staging
- ✅ Supports manual production deployment

### **Pipeline Stages**
1. **Backend Tests**: Python tests with coverage
2. **Frontend Tests**: React tests with coverage
3. **Integration Tests**: End-to-end API testing
4. **Security Scan**: Vulnerability scanning
5. **Performance Test**: Load testing
6. **Staging Deploy**: Automated staging deployment
7. **Production Deploy**: Manual production deployment

## 🆘 Troubleshooting

### **Common Issues**

#### **Database Connection Issues**
```bash
# Check database connectivity
python -c "from core.database import check_database_connection; print(check_database_connection())"

# Verify environment variables
echo $DATABASE_URL
```

#### **Redis Connection Issues**
```bash
# Test Redis connectivity
python -c "import redis; r = redis.from_url(os.getenv('REDIS_URL')); print(r.ping())"
```

#### **Application Startup Issues**
```bash
# Check logs
tail -f /var/log/namaskah/app.log

# Validate configuration
python scripts/setup_production_deployment.py
```

### **Performance Issues**
- Monitor database query performance
- Check Redis memory usage
- Review application logs for bottlenecks
- Scale resources as needed

## 📞 Support & Maintenance

### **Monitoring Dashboards**
- Sentry: Error tracking and performance
- Application logs: Structured logging
- Health endpoints: System status monitoring

### **Backup & Recovery**
- Daily database backups
- Configuration backups
- Disaster recovery procedures

### **Updates & Maintenance**
- Zero-downtime deployments
- Rolling updates for scalability
- Automated rollback procedures

## 🎯 Success Metrics

### **Production Readiness Checklist**
- [x] All tests passing (unit, integration, e2e)
- [x] Security scanning clean
- [x] Performance benchmarks met
- [x] Monitoring configured
- [x] Backup strategy implemented
- [x] Documentation complete

### **Key Performance Indicators**
- **Uptime**: 99.9% SLA
- **Response Time**: <100ms API responses
- **Error Rate**: <0.1% error rate
- **Concurrent Users**: Support 1000+ users
- **Security**: Zero critical vulnerabilities

---

## 🚀 Ready for Production!

Your Namaskah.App enterprise platform is now ready for production deployment. The system includes:

- ✅ **Enterprise-grade architecture** with multi-tenancy and RBAC
- ✅ **Real-time communication** with WebRTC voice/video calling
- ✅ **AI-powered features** for intelligent routing and analytics
- ✅ **Production monitoring** with Sentry and comprehensive logging
- ✅ **Security hardening** with SSL, CORS, and rate limiting
- ✅ **Scalable infrastructure** ready for high-traffic deployments

**Next Steps:**
1. Set up your preferred cloud provider (Render recommended)
2. Configure environment variables
3. Run the deployment scripts
4. Test the deployment thoroughly
5. Go live! 🎉

For additional support or custom deployment requirements, please refer to the codebase documentation or contact the development team.
