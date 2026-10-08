"""
TrustLens Development Orchestrator.
Runs the FastAPI AIML Backend (port 8000) and Vite Frontend (port 3000) concurrently.
"""
import subprocess
import sys
import time
import signal
import os

def main():
    print("=" * 60)
    print("TrustLens AIML Prototype - Phase 1 Development Server")
    print("FastAPI Backend: http://localhost:8000 (API & Docs: /docs)")
    print("Vite Frontend:   http://localhost:3000 (Proxies /api to 8000)")
    print("=" * 60)

    # Launch FastAPI Backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(backend_cmd)

    # Launch Vite Frontend (shell=True on Windows for npx/npm)
    frontend_cmd = "npx vite --port 3000"
    frontend_proc = subprocess.Popen(frontend_cmd, shell=True)

    def cleanup(signum=None, frame=None):
        print("\n[trustlens] Shutting down services...")
        try:
            backend_proc.terminate()
        except Exception:
            pass
        try:
            frontend_proc.terminate()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        while True:
            # Check if any process terminated unexpectedly
            if backend_proc.poll() is not None:
                print(f"[trustlens] Backend process exited with code {backend_proc.returncode}")
                cleanup()
            if frontend_proc.poll() is not None:
                print(f"[trustlens] Frontend process exited with code {frontend_proc.returncode}")
                cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
