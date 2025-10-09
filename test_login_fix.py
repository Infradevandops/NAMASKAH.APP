#!/usr/bin/env python3
"""
Quick test to verify login functionality works
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_login():
    """Test the login functionality"""
    
    # Setup Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("🔍 Testing Login Functionality...")
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000", timeout=5)
            print(f"   ✅ Server is running (Status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Server not accessible: {e}")
            return False
        
        # Navigate to login page
        driver.get("http://localhost:8000/login")
        
        # Wait for login form
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        
        print("   ✅ Login page loaded")
        
        # Fill in credentials
        email_input.send_keys("demo@namaskah.com")
        
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("demo123")
        
        print("   ✅ Credentials entered")
        
        # Submit form
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        print("   ⏳ Login submitted, waiting for redirect...")
        
        # Wait for redirect to dashboard (or any page change)
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "/dashboard" in d.current_url or "/chat" in d.current_url or d.current_url != "http://localhost:8000/login"
            )
            
            current_url = driver.current_url
            print(f"   ✅ Login successful! Redirected to: {current_url}")
            
            # Check if we can see dashboard content
            if "/dashboard" in current_url:
                dashboard_elements = driver.find_elements(By.CSS_SELECTOR, 'h1, h2, .dashboard')
                if dashboard_elements:
                    print("   ✅ Dashboard content loaded")
                else:
                    print("   ⚠️  Dashboard page loaded but content not found")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Login failed or no redirect: {e}")
            print(f"   Current URL: {driver.current_url}")
            
            # Check for error messages
            error_elements = driver.find_elements(By.CSS_SELECTOR, '.error, .alert, [role="alert"]')
            if error_elements:
                for error in error_elements:
                    print(f"   Error message: {error.text}")
            
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        driver.quit()

def main():
    print("🚀 Testing Login Fix")
    print("=" * 50)
    
    success = test_login()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Login test PASSED!")
        print("\n✅ You can now login with:")
        print("   Email: demo@namaskah.com")
        print("   Password: demo123")
        print("\n🌐 Go to: http://localhost:8000/login")
    else:
        print("❌ Login test FAILED!")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Make sure server is running: python start_app.py")
        print("   2. Check browser console for errors")
        print("   3. Try clearing browser cache")
        print("   4. Verify the app compiled without errors")

if __name__ == "__main__":
    main()