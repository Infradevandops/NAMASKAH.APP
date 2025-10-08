#!/usr/bin/env python3
"""
Google OAuth 2.0 Quick Setup Script
"""
import os
import sys

def setup_google_oauth():
    print("🔑 Google OAuth 2.0 Setup for Namaskah.App")
    print("=" * 50)
    print()
    
    print("📋 Before starting, make sure you have:")
    print("1. ✅ Google Cloud Console account")
    print("2. ✅ Created a project")
    print("3. ✅ Enabled Google+ API")
    print("4. ✅ Created OAuth 2.0 credentials")
    print()
    
    # Get credentials from user
    print("🔑 Enter your Google OAuth credentials:")
    client_id = input("Google Client ID: ").strip()
    
    if not client_id:
        print("❌ Client ID is required!")
        return False
    
    client_secret = input("Google Client Secret: ").strip()
    
    if not client_secret:
        print("❌ Client Secret is required!")
        return False
    
    # Validate format
    if not client_id.endswith('.apps.googleusercontent.com'):
        print("⚠️  Warning: Client ID format looks incorrect")
        print("   Expected format: 123456789-abc...xyz.apps.googleusercontent.com")
        
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
    
    if not client_secret.startswith('GOCSPX-'):
        print("⚠️  Warning: Client Secret format looks incorrect")
        print("   Expected format: GOCSPX-abcdefghijklmnopqrstuvwxyz")
        
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
    
    # Set redirect URI
    environment = input("Environment (dev/prod) [dev]: ").strip().lower() or 'dev'
    
    if environment == 'prod':
        domain = input("Production domain (e.g., namaskah.onrender.com): ").strip()
        redirect_uri = f"https://{domain}/api/auth/google/callback"
    else:
        redirect_uri = "http://localhost:8000/api/auth/google/callback"
    
    print()
    print("📝 Configuration Summary:")
    print(f"   Client ID: {client_id[:20]}...{client_id[-20:]}")
    print(f"   Client Secret: {client_secret[:10]}...{client_secret[-5:]}")
    print(f"   Redirect URI: {redirect_uri}")
    print()
    
    confirm = input("Save this configuration? (Y/n): ").strip().lower()
    if confirm == 'n':
        print("❌ Setup cancelled")
        return False
    
    # Update .env file
    env_lines = []
    env_file = '.env'
    
    # Read existing .env
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Remove existing Google OAuth lines
    env_lines = [line for line in env_lines if not line.startswith('GOOGLE_')]
    
    # Add new Google OAuth configuration
    google_config = f"""
# Google OAuth 2.0 Configuration
GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}
GOOGLE_REDIRECT_URI={redirect_uri}
"""
    
    # Write updated .env
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
        f.write(google_config)
    
    print("✅ Google OAuth configured successfully!")
    print()
    print("🚀 Next steps:")
    print("1. Restart your server: uvicorn main:app --reload")
    print("2. Test configuration: curl http://localhost:8000/api/auth/google/config")
    print("3. Test OAuth flow: open http://localhost:8000/api/auth/google/login")
    print()
    print("📚 Need help? Check GOOGLE_OAUTH_SETUP_GUIDE.md")
    
    return True

def test_configuration():
    """Test if Google OAuth is properly configured"""
    print("🧪 Testing Google OAuth Configuration...")
    
    # Check environment variables
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    if not client_id:
        print("❌ GOOGLE_CLIENT_ID not found in environment")
        return False
    
    if not client_secret:
        print("❌ GOOGLE_CLIENT_SECRET not found in environment")
        return False
    
    if not redirect_uri:
        print("❌ GOOGLE_REDIRECT_URI not found in environment")
        return False
    
    print("✅ All Google OAuth environment variables found")
    print(f"   Client ID: {client_id[:20]}...{client_id[-20:]}")
    print(f"   Redirect URI: {redirect_uri}")
    
    # Test API endpoint (if server is running)
    try:
        import requests
        response = requests.get('http://localhost:8000/api/auth/google/config', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('configured'):
                print("✅ Google OAuth API endpoint configured correctly")
                return True
            else:
                print("❌ Google OAuth API endpoint reports not configured")
                return False
        else:
            print("⚠️  Server not running or endpoint not accessible")
            print("   Start server with: uvicorn main:app --reload")
            return True  # Config is still valid
            
    except ImportError:
        print("⚠️  requests library not available for testing")
        print("   Install with: pip install requests")
        return True
    except Exception as e:
        print(f"⚠️  Could not test API endpoint: {e}")
        print("   Make sure server is running")
        return True
    
    return True

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        test_configuration()
    else:
        setup_google_oauth()

if __name__ == "__main__":
    main()