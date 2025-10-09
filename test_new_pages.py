#!/usr/bin/env python3
"""
Test script to verify the new About and Reviews pages work
"""
import requests
import time

def test_new_pages():
    """Test if the new About and Reviews pages are accessible"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing New Pages...")
    print("=" * 40)
    
    # Test new pages
    new_pages = ["/about", "/reviews"]
    
    for page in new_pages:
        try:
            url = f"{base_url}{page}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                # Check if it contains React app content
                if "namaskah" in response.text and ("About" in response.text or "Reviews" in response.text):
                    print(f"✅ {page} - New page loaded successfully")
                else:
                    print(f"⚠️  {page} - Loaded but content may not be correct")
            else:
                print(f"❌ {page} - Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {page} - Error: {e}")
    
    print("\n🔗 Testing Navigation Links...")
    
    # Test if landing page has links to new pages
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            
            if "about" in content:
                print("✅ Landing page has About link")
            else:
                print("⚠️  Landing page missing About link")
                
            if "reviews" in content:
                print("✅ Landing page has Reviews link")
            else:
                print("⚠️  Landing page missing Reviews link")
        else:
            print("❌ Could not load landing page")
            
    except Exception as e:
        print(f"❌ Navigation test failed: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Test Summary:")
    print("- About page should load with company information")
    print("- Reviews page should load with customer testimonials")
    print("- Navigation should work between all pages")
    print(f"\n🌐 Test manually at: {base_url}/about and {base_url}/reviews")

if __name__ == "__main__":
    test_new_pages()