# 🔑 Google OAuth 2.0 Setup Guide

## 📋 **Step-by-Step Instructions**

### **Step 1: Go to Google Cloud Console**
1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account

### **Step 2: Create or Select Project**
1. Click the project dropdown (top left)
2. Click **"New Project"** or select existing project
3. Enter project name: `Namaskah-App` (or your preferred name)
4. Click **"Create"**

### **Step 3: Enable Google+ API**
1. In the left sidebar, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google+ API"**
3. Click on **"Google+ API"**
4. Click **"Enable"**

### **Step 4: Create OAuth 2.0 Credentials**
1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"**
3. Select **"OAuth 2.0 Client IDs"**

### **Step 5: Configure OAuth Consent Screen**
1. If prompted, click **"Configure Consent Screen"**
2. Select **"External"** (for public use)
3. Fill required fields:
   - **App name:** `Namaskah.App`
   - **User support email:** Your email
   - **Developer contact:** Your email
4. Click **"Save and Continue"**
5. Skip **"Scopes"** → Click **"Save and Continue"**
6. Skip **"Test users"** → Click **"Save and Continue"**

### **Step 6: Create OAuth Client ID**
1. Back to **"Credentials"** → **"+ CREATE CREDENTIALS"** → **"OAuth 2.0 Client IDs"**
2. Select **"Web application"**
3. Enter name: `Namaskah-App-Web`
4. **Authorized redirect URIs:** Add these URLs:
   ```
   http://localhost:8000/api/auth/google/callback
   https://yourdomain.com/api/auth/google/callback
   ```
5. Click **"Create"**

### **Step 7: Get Your Keys**
After creation, you'll see a popup with:
- **Client ID:** `123456789-abcdefghijklmnop.apps.googleusercontent.com`
- **Client Secret:** `GOCSPX-abcdefghijklmnopqrstuvwxyz`

**⚠️ IMPORTANT:** Copy these immediately - you won't see the secret again!

---

## 🔧 **Configuration**

### **Step 8: Set Environment Variables**

Add these to your `.env` file:

```bash
# Google OAuth 2.0 Configuration
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

### **Step 9: Update Production URLs**
For production, update redirect URI in Google Console:
```
https://namaskah.onrender.com/api/auth/google/callback
```

And update `.env.production`:
```bash
GOOGLE_REDIRECT_URI=https://namaskah.onrender.com/api/auth/google/callback
```

---

## ✅ **Verification**

### **Step 10: Test Configuration**
```bash
# Check if OAuth is configured
curl http://localhost:8000/api/auth/google/config

# Should return:
{
  "configured": true,
  "client_id": "123456789-abcdefghijklmnop.apps.googleusercontent.com",
  "redirect_uri": "http://localhost:8000/api/auth/google/callback"
}
```

### **Step 11: Test OAuth Flow**
```bash
# Get OAuth URL
curl http://localhost:8000/api/auth/google/login

# Should return:
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...",
  "state": "random_state_string",
  "message": "Redirect user to auth_url to complete Google OAuth flow"
}
```

---

## 🎯 **Quick Setup Script**

Save this as `setup_google_oauth.py`:

```python
#!/usr/bin/env python3
import os

def setup_google_oauth():
    print("🔑 Google OAuth 2.0 Setup")
    print("=" * 40)
    
    client_id = input("Enter Google Client ID: ").strip()
    client_secret = input("Enter Google Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both Client ID and Secret are required!")
        return
    
    # Update .env file
    env_content = f"""
# Google OAuth 2.0 Configuration
GOOGLE_CLIENT_ID={client_id}
GOOGLE_CLIENT_SECRET={client_secret}
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
"""
    
    with open('.env', 'a') as f:
        f.write(env_content)
    
    print("✅ Google OAuth configured successfully!")
    print("🚀 Restart your server to apply changes")

if __name__ == "__main__":
    setup_google_oauth()
```

Run with: `python setup_google_oauth.py`

---

## 🔍 **What Keys You Need**

### **Required Keys:**
1. **GOOGLE_CLIENT_ID** 
   - Format: `123456789-abcdefghijklmnop.apps.googleusercontent.com`
   - Used to identify your app to Google

2. **GOOGLE_CLIENT_SECRET**
   - Format: `GOCSPX-abcdefghijklmnopqrstuvwxyz`
   - Used to authenticate your app with Google

3. **GOOGLE_REDIRECT_URI**
   - Format: `http://localhost:8000/api/auth/google/callback`
   - Where Google sends users after authentication

### **Optional (Auto-configured):**
- **GOOGLE_AUTH_URL** - Auto-set to Google's OAuth endpoint
- **GOOGLE_TOKEN_URL** - Auto-set to Google's token endpoint
- **GOOGLE_USER_INFO_URL** - Auto-set to Google's user info endpoint

---

## ⚡ **Quick Test**

After setup, test immediately:

```bash
# 1. Start server
source .venv/bin/activate
python -m uvicorn main:app --reload

# 2. Test in browser
open http://localhost:8000/api/auth/google/login

# 3. Should redirect to Google login
```

---

## 🚨 **Common Issues**

### **Issue 1: "redirect_uri_mismatch"**
**Solution:** Ensure redirect URI in Google Console exactly matches your `.env` file

### **Issue 2: "invalid_client"**
**Solution:** Check Client ID and Secret are correct and not expired

### **Issue 3: "access_denied"**
**Solution:** User cancelled login - this is normal behavior

---

## 📝 **Summary**

**You need exactly 2 keys from Google:**
1. **Client ID** (public identifier)
2. **Client Secret** (private key)

**Total setup time:** ~10 minutes

**Ready to use after:** Setting environment variables and restarting server

🎉 **Your Google OAuth 2.0 will be fully functional!**