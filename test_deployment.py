#!/usr/bin/env python3
"""Quick deployment test script"""
import asyncio
import httpx

BASE_URL = "https://your-app.onrender.com"  # Replace with your actual URL

async def test_deployment():
    async with httpx.AsyncClient() as client:
        # Health check
        print("🏥 Testing health...")
        health = await client.get(f"{BASE_URL}/health")
        print(f"Health: {health.status_code}")
        
        # Register user
        print("👤 Testing registration...")
        register = await client.post(f"{BASE_URL}/api/auth/register", json={
            "email": "test@example.com",
            "password": "Test123!",
            "full_name": "Test User"
        })
        print(f"Register: {register.status_code}")
        
        # SMS verification
        print("📱 Testing SMS verification...")
        sms = await client.post(f"{BASE_URL}/api/verification/create", json={
            "service_name": "whatsapp",
            "capability": "sms"
        })
        print(f"SMS: {sms.status_code}")
        
        print("✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_deployment())