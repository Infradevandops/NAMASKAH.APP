#!/usr/bin/env python3
"""
Simple webhook test script
"""
import json
import requests

def test_webhook():
    """Test TextVerified webhook endpoint"""
    url = "http://localhost:8000/api/webhooks/textverified"
    
    payload = {
        "id": "test_verification_123",
        "status": "completed", 
        "service": "whatsapp",
        "number": "+1234567890",
        "messages": [{"text": "Your verification code is: 123456"}]
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_webhook()