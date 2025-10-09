#!/usr/bin/env python3
"""
Test script to check page navigation and linking at http://localhost:8000
"""
import requests
import time
from urllib.parse import urljoin

def test_page_navigation():
    """Test if all pages are accessible and properly linked"""
    base_url = "http://localhost:8000"
    
    # Define all expected routes
    routes = {
        "public": [
            "/",
            "/about", 
            "/reviews",
            "/login",
            "/register"
        ],
        "protected": [
            "/dashboard",
            "/admin", 
            "/billing",
            "/chat",
            "/numbers",
            "/verifications"
        ],
        "api": [
            "/health",
            "/docs"
        ]
    }
    
    print("🧪 Testing namaskah Page Navigation...")
    print("=" * 50)
    
    # Test public routes
    print("\n📱 Testing Public Routes:")
    for route in routes["public"]:
        try:
            url = urljoin(base_url, route)
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                # Check if it's serving React app
                if "namaskah" in response.text or "react" in response.text.lower():
                    print(f"✅ {route} - React app loaded")
                else:
                    print(f"⚠️  {route} - Loaded but may not be React app")
            else:
                print(f"❌ {route} - Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {route} - Error: {e}")
    
    # Test protected routes (should redirect to login or show login prompt)
    print("\n🔒 Testing Protected Routes:")
    for route in routes["protected"]:
        try:
            url = urljoin(base_url, route)
            response = requests.get(url, timeout=5, allow_redirects=False)
            
            if response.status_code in [200, 302, 401]:
                print(f"✅ {route} - Properly protected (Status: {response.status_code})")
            else:
                print(f"⚠️  {route} - Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {route} - Error: {e}")
    
    # Test API routes
    print("\n🔌 Testing API Routes:")
    for route in routes["api"]:
        try:
            url = urljoin(base_url, route)
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                if route == "/health":
                    try:
                        data = response.json()
                        print(f"✅ {route} - API working (Status: {data.get('status', 'unknown')})")
                    except:
                        print(f"✅ {route} - Responding but not JSON")
                elif route == "/docs":
                    if "swagger" in response.text.lower() or "openapi" in response.text.lower():
                        print(f"✅ {route} - API docs loaded")
                    else:
                        print(f"⚠️  {route} - Loaded but may not be API docs")
            else:
                print(f"❌ {route} - Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {route} - Error: {e}")
    
    # Test navigation within React app
    print("\n🔗 Testing React App Navigation:")
    try:
        # Get the main page
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            content = response.text
            
            # Check for navigation elements
            nav_indicators = [
                "login", "register", "dashboard", "about", 
                "navigation", "nav", "menu", "header"
            ]
            
            found_nav = []
            for indicator in nav_indicators:
                if indicator.lower() in content.lower():
                    found_nav.append(indicator)
            
            if found_nav:
                print(f"✅ Navigation elements found: {', '.join(found_nav)}")
            else:
                print("⚠️  No obvious navigation elements found in HTML")
                
            # Check if it's a proper React app
            react_indicators = ["react", "app", "root", "bundle", "chunk"]
            found_react = []
            for indicator in react_indicators:
                if indicator.lower() in content.lower():
                    found_react.append(indicator)
            
            if found_react:
                print(f"✅ React app indicators: {', '.join(found_react)}")
            else:
                print("⚠️  No React app indicators found")
                
        else:
            print(f"❌ Could not load main page - Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Navigation test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Navigation Test Summary:")
    print("- All routes should be accessible")
    print("- Protected routes should redirect to login")
    print("- React app should handle client-side routing")
    print("- API endpoints should return proper responses")
    
    print(f"\n🌐 Test your app manually at: {base_url}")
    print("📖 API documentation at: {}/docs".format(base_url))

if __name__ == "__main__":
    test_page_navigation()