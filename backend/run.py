#!/usr/bin/env python3
"""
Project AETHER - Startup Script
"""

import uvicorn
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Set default port
    port = int(os.getenv("PORT", 8000))
    # On Windows, use 127.0.0.1 instead of 0.0.0.0 to avoid permission issues
    # Can still override with HOST env var if needed
    default_host = "127.0.0.1" if sys.platform == "win32" else "0.0.0.0"
    host = os.getenv("HOST", default_host)
    
    print("=" * 50)
    print("⚡ PROJECT AETHER - Starting Server")
    print("=" * 50)
    print(f"Server will run on http://{host}:{port}")
    print(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'huggingface')}")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            reload=False,  # Disabled reload to prevent issues
            log_level="info"
        )
    except OSError as e:
        if "10013" in str(e) or "permission" in str(e).lower():
            print("\n❌ ERROR: Port access denied!")
            print(f"Port {port} may be in use or blocked by Windows Firewall.")
            print("\nSolutions:")
            print(f"1. Kill the process using port {port}:")
            print(f"   netstat -ano | findstr :{port}")
            print(f"   taskkill /PID <PID> /F")
            print(f"2. Use a different port:")
            print(f"   set PORT=8001")
            print(f"   python run.py")
            print(f"3. Run as Administrator")
            sys.exit(1)
        else:
            raise

