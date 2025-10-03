#!/usr/bin/env python3
"""
Start Namaskah.App locally with test environment
"""
import os
import sys

# Set environment variables for local testing
os.environ.update({
    'JWT_SECRET_KEY': 'test_jwt_secret_key_for_local_development_only_32_chars_minimum',
    'DATABASE_URL': 'sqlite:///./namaskah_local.db',
    'USE_MOCK_TWILIO': 'true',
    'USE_MOCK_TEXTVERIFIED': 'true',
    'DEBUG': 'true',
    'LOG_LEVEL': 'INFO',
    'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000',
    'RATE_LIMIT_ENABLED': 'false',
    'ENVIRONMENT': 'development'
})

print("🚀 Starting Namaskah.App in local development mode...")
print("📧 Test Credentials:")
print("   Email: test@namaskah.app")
print("   Password: TestPassword123!")
print("   Username: testuser")
print()
print("🔗 URLs to test:")
print("   App: http://localhost:8000")
print("   API Docs: http://localhost:8000/docs")
print("   Health Check: http://localhost:8000/health")
print("   Detailed Health: http://localhost:8000/health/detailed")
print()

if __name__ == "__main__":
    import uvicorn
    
    # Start the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )