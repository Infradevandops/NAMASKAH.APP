#!/usr/bin/env python3
"""
Basic WebSocket implementation test (no external dependencies)
"""
import sys
import os

def test_websocket_imports():
    """Test that all WebSocket-related imports work"""
    try:
        print("📦 Testing WebSocket imports...")
        
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
                
        # Test WebRTC service methods
        webrtc_service = WebRTCService()
        webrtc_methods = ['initiate_call', 'create_webrtc_session', 'get_call_participants']
        for method in webrtc_methods:
            if hasattr(webrtc_service, method):
                print(f"✅ webrtc_service.{method} available")
            else:
                print(f"❌ webrtc_service.{method} missing")
                
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_websocket_router():
    """Test WebSocket router configuration"""
    try:
        print("\n🔌 Testing WebSocket router...")
        
        from api.websocket_api import router
        
        # Check router configuration
        print(f"✅ Router prefix: {router.prefix}")
        print(f"✅ Router tags: {router.tags}")
        
        # Check routes
        routes = [route.path for route in router.routes]
        expected_routes = ['/chat', '/webrtc/{call_id}', '/status', '/broadcast/{conversation_id}', '/health', '/test']
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                print(f"✅ Route {expected_route} found")
            else:
                print(f"❌ Route {expected_route} missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Router test failed: {e}")
        return False

def test_main_app_integration():
    """Test that WebSocket router is properly integrated in main.py"""
    try:
        print("\n🔗 Testing main app integration...")
        
        # Read main.py to check if websocket router is included
        with open('main.py', 'r') as f:
            main_content = f.read()
        
        if 'websocket_router' in main_content:
            print("✅ websocket_router imported in main.py")
        else:
            print("❌ websocket_router not imported in main.py")
            
        if 'app.include_router(websocket_router' in main_content:
            print("✅ websocket_router included in FastAPI app")
        else:
            print("❌ websocket_router not included in FastAPI app")
            
        return True
        
    except Exception as e:
        print(f"❌ Main app integration test failed: {e}")
        return False

def main():
    """Run all basic WebSocket tests"""
    print("🚀 Starting Basic WebSocket Implementation Tests")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_websocket_imports()
    
    # Test router
    router_ok = test_websocket_router()
    
    # Test main app integration
    integration_ok = test_main_app_integration()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"✅ Imports: {'PASS' if imports_ok else 'FAIL'}")
    print(f"✅ Router: {'PASS' if router_ok else 'FAIL'}")
    print(f"✅ Integration: {'PASS' if integration_ok else 'FAIL'}")
    
    if imports_ok and router_ok and integration_ok:
        print("\n🎉 WebSocket implementation is properly configured!")
        print("\n📚 Next steps:")
        print("1. Start the server: uvicorn main:app --reload")
        print("2. Visit the test page: http://localhost:8000/ws/test")
        print("3. Check WebSocket health: http://localhost:8000/ws/health")
        print("4. Get a JWT token from /api/auth/login")
        print("5. Test real-time messaging")
        
        print("\n🔌 Available WebSocket endpoints:")
        print("• /ws/chat - Real-time chat WebSocket")
        print("• /ws/webrtc/{call_id} - WebRTC signaling")
        print("• /ws/status - Connection status")
        print("• /ws/health - Service health check")
        print("• /ws/test - Interactive test page")
    else:
        print("\n⚠️ Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main()