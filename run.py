#!/usr/bin/env python3
"""
Amazon Web Crawler Runner
Sets up the environment and launches the application.
"""

import subprocess
import sys
import os
import time
import webbrowser

def check_venv():
    """Check if virtual environment is activated"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Please activate the virtual environment first:")
        print("   source venv/bin/activate")
        sys.exit(1)
    print("✅ Virtual environment is active")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def install_playwright():
    """Install Playwright browsers"""
    print("🎭 Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        print("✅ Playwright browsers installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        sys.exit(1)

def start_backend():
    """Start the Flask backend server"""
    print("🚀 Starting Flask backend server...")
    try:
        # Start backend in background
        backend_process = subprocess.Popen([sys.executable, "backend/app.py"])
        print("✅ Backend server started on http://localhost:5001")
        return backend_process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        sys.exit(1)

def open_frontend():
    """Open the frontend in browser"""
    print("🌐 Opening frontend in browser...")
    try:
        # Give server a moment to start
        time.sleep(3)
        # Open index.html in default browser
        webbrowser.open(f"file://{os.path.abspath('index.html')}")
        print("✅ Frontend opened in browser")
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"   Please manually open: file://{os.path.abspath('index.html')}")

def main():
    print("🎯 Amazon Web Crawler Launcher")
    print("=" * 40)

    # Check virtual environment
    check_venv()

    # Install dependencies
    install_dependencies()

    # Install Playwright
    install_playwright()

    # Start backend
    backend_process = start_backend()

    # Open frontend
    open_frontend()

    print("\n🎉 Application is ready!")
    print("   Backend: http://localhost:5001")
    print("   Frontend: Opened in browser")
    print("\n💡 To test: Enter a search term like 'wireless headphones' in the search box")
    print("   Press Ctrl+C to stop the server")

    try:
        # Keep the script running
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        backend_process.terminate()
        backend_process.wait()
        print("✅ Server stopped. Goodbye!")

if __name__ == "__main__":
    main()
