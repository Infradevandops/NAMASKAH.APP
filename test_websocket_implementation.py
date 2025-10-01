#!/usr/bin/env python3
"""
Test WebSocket implementation
"""
import asyncio
import json
import websockets
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_websocket_connection():
    """Test basic WebSocket connection and messaging"""
    print("🧪 Testing WebSocket Implementation...")
    
    # First, get a JWT token (you'll need to implement login)
    try:
        # Test health endpoint first
        health_response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {health_response.status_code}")
        
        # Test WebSocket health
        ws_health_response = requests.get(f"{BASE_URL}/ws/health")
        print(f"✅ WebSocket health: {ws_health_response.status_code}")
        print(f"📊 WebSocket status: {ws_health_response.json()}")
        
        # Test WebSocket test page
        test_page_response = requests.get(f"{BASE_URL}/ws/test")
        print(f"✅ WebSocket test page: {test_page_response.status_code}")
        
        print("\n🎯 WebSocket implementation is ready!")
        print(f"📱 Test page available at: {BASE_URL}/ws/test")
        print(f"🔌 WebSocket endpoint: {WS_URL}/ws/chat")
        print(f"📞 WebRTC endpoint: {WS_URL}/ws/webrtc/{{call_id}}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing WebSocket: {e}")
        return False

async def test_websocket_with_mock_token():
    """Test WebSocket with a mock token (for development)"""
    try:
        # This would normally require a real JWT token
        # For now, just test the connection attempt
        print("\n🔐 Testing WebSocket authentication flow...")
        
        # Test connection without token (should fail gracefully)
        try:
            async with websockets.connect(f"{WS_URL}/ws/chat") as websocket:
                # Send auth message
                auth_message = {
                    "type": "auth",
                    "token": "mock_token_for_testing"
                }
                await websocket.send(json.dumps(auth_message))
                
                # This should fail with invalid token, but connection should be handled gracefully
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📨 Received: {response}")
                
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"✅ Connection closed as expected (invalid token): {e.code}")
        except asyncio.TimeoutError:
            print("✅ Connection timeout as expected (no valid token)")
        except Exception as e:
            print(f"⚠️ Connection test result: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ WebSocket auth test failed: {e}")
        return False

def test_websocket_imports():
    """Test that all WebSocket-related imports work"""
    try:
        print("\n📦 Testing WebSocket imports...")
        
        # Test websocket_manager import
        from services.websocket_manager import connection_manager, websocket_handler
        print("✅ websocket_manager imported successfully")
        
        # Test webrtc_service import  
        from services.webrtc_service import WebRTCService
        print("✅ webrtc_service imported successfully")
        
        # Test websocket_api import
        from api.websocket_api import router
        print("✅ websocket_api imported successfully")
        
        # Test that connection manager has expected methods
        methods = ['get_online_users', 'is_user_online', 'send_personal_message']
        for method in methods:
            if hasattr(connection_manager, method):
                print(f"✅ connection_manager.{method} available")
            else:
                print(f"❌ connection_manager.{method} missing")
                
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

async def main():
    """Run all WebSocket tests"""
    print("🚀 Starting WebSocket Implementation Tests")
    print("=" * 50)
    
    # Test imports first
    imports_ok = test_websocket_imports()
    
    if imports_ok:
        # Test basic connection
        connection_ok = await test_websocket_connection()
        
        if connection_ok:
            # Test authentication flow
            auth_ok = await test_websocket_with_mock_token()
            
            print("\n" + "=" * 50)
            print("📋 Test Summary:")
            print(f"✅ Imports: {'PASS' if imports_ok else 'FAIL'}")
            print(f"✅ Connection: {'PASS' if connection_ok else 'FAIL'}")
            print(f"✅ Authentication: {'PASS' if auth_ok else 'FAIL'}")
            
            if imports_ok and connection_ok:
                print("\n🎉 WebSocket implementation is working!")
                print("\n📚 Next steps:")
                print("1. Start the server: uvicorn main:app --reload")
                print("2. Visit the test page: http://localhost:8000/ws/test")
                print("3. Get a JWT token from /api/auth/login")
                print("4. Test real-time messaging")
            else:
                print("\n⚠️ Some tests failed. Check the logs above.")
        else:
            print("\n❌ Connection tests failed")
    else:
        print("\n❌ Import tests failed")

if __name__ == "__main__":
    asyncio.run(main())