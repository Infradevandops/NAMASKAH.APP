# 🔧 namaskah Troubleshooting Guide

## 🚨 Issue: localhost:8000 shows nothing

### **Step 1: Verify Server is Starting**

Run this command to check if the server starts:
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**If you see errors:**
- Import errors → Run diagnostics (see Step 2)
- Port already in use → Use different port: `--port 8001`
- Module not found → Install dependencies (see Step 3)

### **Step 2: Run Diagnostics**

```bash
python3 diagnose.py
```

This will check:
- ✅ Python version and environment
- ✅ File structure (main.py, React build)
- ✅ Import issues
- ✅ Required packages

### **Step 3: Install Dependencies**

If packages are missing:
```bash
# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### **Step 4: Rebuild React App**

If React build is missing or corrupted:
```bash
cd frontend
npm install
npm run build
cd ..
```

### **Step 5: Test Simple Server**

Test with minimal server:
```bash
python3 simple_server_test.py
```

Visit: http://localhost:8001

**If this works but main server doesn't** → Import issue in main.py

### **Step 6: Check Browser Console**

1. Open browser developer tools (F12)
2. Go to Console tab
3. Visit http://localhost:8000
4. Look for JavaScript errors

**Common errors:**
- `Failed to load resource` → Static files not served correctly
- `Uncaught ReferenceError` → React build issue
- `Network error` → Server not running

### **Step 7: Test Individual Routes**

Test these URLs directly:

1. **Health Check**: http://localhost:8000/health
   - Should return JSON: `{"status": "healthy", ...}`
   
2. **API Docs**: http://localhost:8000/docs
   - Should show FastAPI documentation
   
3. **Static Files**: http://localhost:8000/static/css/main.6ad5dda4.css
   - Should return CSS content

**If any fail** → Route configuration issue

### **Step 8: Check Server Logs**

Look for these in server output:
```
INFO:     "GET / HTTP/1.1" 200 OK          # ✅ Good
INFO:     "GET / HTTP/1.1" 404 Not Found   # ❌ Route issue
INFO:     "GET / HTTP/1.1" 500 Internal    # ❌ Server error
```

---

## 🛠️ **Quick Fixes**

### **Fix 1: Route Order Issue**
The catch-all route `/{full_path:path}` might be interfering. 

**Solution**: Move specific routes BEFORE catch-all route in main.py

### **Fix 2: Static File Path Issue**
React build references `/static/` but FastAPI serves from different path.

**Solution**: Check `app.mount("/static", ...)` configuration

### **Fix 3: CORS Issue**
Browser blocks requests due to CORS policy.

**Solution**: Check CORS middleware in `core/middleware.py`

### **Fix 4: React Build Issue**
React app built incorrectly or missing chunks.

**Solution**: 
```bash
cd frontend
rm -rf build node_modules
npm install
npm run build
```

---

## 🎯 **Most Likely Solutions**

### **Solution A: Fresh Start**
```bash
# 1. Stop any running servers
# 2. Rebuild everything
cd frontend && npm run build && cd ..
# 3. Start server
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **Solution B: Development Mode**
If React build is problematic, run React separately:
```bash
# Terminal 1: Start backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start React dev server
cd frontend && npm start
```
Then visit: http://localhost:3000 (React dev server)

### **Solution C: Minimal Test**
```bash
# Test with simple server first
python3 simple_server_test.py
# Visit: http://localhost:8001
```

---

## 📞 **Still Not Working?**

### **Check These:**

1. **Firewall/Antivirus**: Blocking port 8000
2. **Other Services**: Something else using port 8000
3. **Virtual Environment**: Not activated properly
4. **File Permissions**: Can't read React build files
5. **Browser Cache**: Clear cache and hard refresh (Ctrl+F5)

### **Get More Info:**
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Check file permissions
ls -la frontend/build/

# Test with curl
curl http://localhost:8000
curl http://localhost:8000/health
```

---

## ✅ **Success Indicators**

When working correctly, you should see:

1. **Server starts** without errors
2. **http://localhost:8000** shows React app (namaskah landing page)
3. **http://localhost:8000/docs** shows API documentation
4. **http://localhost:8000/health** returns JSON health status
5. **Browser console** shows no errors
6. **React navigation** works (clicking links changes URL)

---

**🎯 Most common issue**: Route configuration or React build problems
**🔧 Quick fix**: Rebuild React app and restart server
**📞 Need help**: Run `python3 diagnose.py` and share the output