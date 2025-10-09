#!/usr/bin/env python3
"""
Build verification script for namaskah deployment
"""
import os
import sys
import json
from pathlib import Path

def verify_frontend_build():
    """Verify that frontend build is complete and valid"""
    print("🔍 Verifying frontend build...")
    
    # Check if build directory exists
    build_dir = Path("frontend/build")
    if not build_dir.exists():
        print("❌ Frontend build directory not found")
        return False
    
    # Check if index.html exists
    index_file = build_dir / "index.html"
    if not index_file.exists():
        print("❌ index.html not found in build directory")
        return False
    
    # Check if static directory exists
    static_dir = build_dir / "static"
    if not static_dir.exists():
        print("❌ Static directory not found")
        return False
    
    # Check for JS and CSS files
    js_dir = static_dir / "js"
    css_dir = static_dir / "css"
    
    if not js_dir.exists():
        print("❌ JS directory not found")
        return False
    
    if not css_dir.exists():
        print("❌ CSS directory not found")
        return False
    
    # Count files
    js_files = list(js_dir.glob("*.js"))
    css_files = list(css_dir.glob("*.css"))
    
    print(f"✅ Found {len(js_files)} JS files")
    print(f"✅ Found {len(css_files)} CSS files")
    
    # Verify index.html references
    with open(index_file, 'r') as f:
        content = f.read()
    
    # Check if main JS file is referenced
    main_js_files = [f for f in js_files if f.name.startswith('main.')]
    if not main_js_files:
        print("❌ No main JS file found")
        return False
    
    main_js = main_js_files[0]
    if f"/static/js/{main_js.name}" not in content:
        print(f"❌ Main JS file {main_js.name} not referenced in index.html")
        return False
    
    # Check if main CSS file is referenced
    main_css_files = [f for f in css_files if f.name.startswith('main.')]
    if not main_css_files:
        print("❌ No main CSS file found")
        return False
    
    main_css = main_css_files[0]
    if f"/static/css/{main_css.name}" not in content:
        print(f"❌ Main CSS file {main_css.name} not referenced in index.html")
        return False
    
    print("✅ Frontend build verification passed")
    return True

def verify_backend():
    """Verify backend dependencies"""
    print("🔍 Verifying backend...")
    
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI and Uvicorn available")
    except ImportError as e:
        print(f"❌ Backend dependency missing: {e}")
        return False
    
    # Check if main.py exists
    if not os.path.exists("main.py"):
        print("❌ main.py not found")
        return False
    
    print("✅ Backend verification passed")
    return True

def main():
    """Main verification function"""
    print("🚀 namaskah Build Verification")
    print("=" * 40)
    
    backend_ok = verify_backend()
    frontend_ok = verify_frontend_build()
    
    print("=" * 40)
    if backend_ok and frontend_ok:
        print("✅ All verifications passed - ready for deployment!")
        sys.exit(0)
    else:
        print("❌ Verification failed - check errors above")
        sys.exit(1)

if __name__ == "__main__":
    main()