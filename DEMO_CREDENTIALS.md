# 🔐 namaskah Demo Credentials & Authentication Guide

## 🚀 **Quick Start - Demo Login**

### **Current Authentication Status**
- ✅ **Frontend**: Complete login/register forms
- ✅ **Mock Auth**: Any credentials work for testing
- ⚠️ **Backend**: Simulated authentication (not connected to real database)
- ⚠️ **Social Login**: UI ready but not connected to OAuth providers

---

## 🎯 **Demo Login Options**

### **Option 1: Mock Authentication (Current - Recommended for Testing)**

**Any email/password combination works! Try these:**

```
Email: demo@namaskah.com
Password: demo123

Email: admin@namaskah.com  
Password: admin123

Email: test@example.com
Password: password
```

**How it works:**
- Frontend accepts any valid email format
- Password must be 6+ characters
- Automatically logs you in and redirects to dashboard
- User data is simulated (John Doe, demo@namaskah.com)

### **Option 2: Real Demo Users (Can be implemented)**

If you need real authentication, I can quickly set up:

```
Email: demo@namaskah.com
Password: DemoUser123!
Role: Standard User

Email: admin@namaskah.com
Password: AdminUser123!
Role: Administrator

Email: test@namaskah.com
Password: TestUser123!
Role: Test User
```

---

## 🔧 **How to Test the App**

### **1. Start the Application**
```bash
# Terminal 1: Start backend
python start_app.py

# Terminal 2: Start frontend (if separate)
cd frontend && npm start
```

### **2. Access the Application**
- **URL**: http://localhost:8000
- **Login Page**: http://localhost:8000/login
- **Register Page**: http://localhost:8000/register

### **3. Login Process**
1. Go to http://localhost:8000
2. Click "Login" or "Get Started"
3. Enter any email (e.g., `demo@namaskah.com`)
4. Enter any password 6+ chars (e.g., `demo123`)
5. Click "Sign in"
6. You'll be redirected to the dashboard

### **4. Available Features After Login**
- ✅ **Dashboard**: Analytics and overview
- ✅ **Chat**: Real-time messaging interface
- ✅ **Phone Numbers**: Number management
- ✅ **Admin Panel**: User management (if admin)
- ✅ **Billing**: Subscription management
- ✅ **Verifications**: SMS verification history

---

## 🌐 **Social Login Status**

### **Google Login**
- ✅ **UI Button**: Ready and styled
- ❌ **OAuth Integration**: Not connected
- 🔧 **To Enable**: Need Google OAuth client ID/secret

### **Twitter Login**  
- ✅ **UI Button**: Ready and styled
- ❌ **OAuth Integration**: Not connected
- 🔧 **To Enable**: Need Twitter API keys

### **GitHub Login** (Can be added)
- ❌ **Not implemented yet**
- 🔧 **Can add**: Easy to implement

---

## 🛠️ **For Developers**

### **Current Auth Flow**
```javascript
// Frontend (useAuth.js)
const login = async (email, password) => {
  // Simulates API call with 1 second delay
  const response = await mockApiCall();
  
  // Stores fake JWT token
  localStorage.setItem('authToken', 'fake-jwt-token');
  
  // Sets user data
  setUser({
    id: 1,
    name: 'John Doe',
    email: email,
    role: 'user'
  });
};
```

### **Backend Auth Endpoints**
```python
# Available endpoints (main.py)
POST /api/auth/login
POST /api/auth/register  
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/refresh
```

### **To Enable Real Authentication**
1. Connect frontend `useAuth.js` to backend APIs
2. Set up database user storage
3. Implement JWT token validation
4. Add OAuth provider configurations

---

## 🎯 **Recommended Approach for Testing**

### **For Rich Text Editor Development**
**Use Mock Authentication** - It's perfect for testing new features:

1. **Quick Login**: `demo@namaskah.com` / `demo123`
2. **Access Chat**: Navigate to chat page
3. **Test Features**: Rich text editor, emoji picker, file uploads
4. **No Setup Required**: Works immediately

### **For Production Deployment**
**Implement Real Authentication**:

1. Connect to backend database
2. Set up OAuth providers
3. Add proper session management
4. Implement security measures

---

## 🚀 **Next Steps**

### **Immediate (For Rich Text Editor)**
- ✅ Use mock authentication for testing
- ✅ Focus on chat functionality enhancement
- ✅ Test with demo credentials above

### **Future (For Production)**
- 🔧 Implement real user database
- 🔧 Connect OAuth providers
- 🔧 Add proper session management
- 🔧 Security hardening

---

## 📞 **Need Help?**

### **Common Issues**
1. **"Invalid email"** - Use proper email format (user@domain.com)
2. **"Password too short"** - Use 6+ characters
3. **"Login failed"** - Any credentials should work in mock mode
4. **"Page not found"** - Make sure server is running on port 8000

### **Quick Fixes**
```bash
# Restart the application
python start_app.py

# Clear browser cache/localStorage
# In browser console:
localStorage.clear()

# Check server status
curl http://localhost:8000/health
```

---

**🎉 Ready to test! Use `demo@namaskah.com` / `demo123` and start exploring the Rich Text Editor features!**