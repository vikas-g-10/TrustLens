"""Runs backend (port 8000) and frontend (port 3000) together for local development."""
import os, signal, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))

def main():
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=os.path.join(ROOT, "backend"),
    )
    frontend = subprocess.Popen("npm run dev", shell=True, cwd=os.path.join(ROOT, "frontend"))

    def stop(*_):
        for p in (backend, frontend):
            try: p.terminate()
            except Exception: pass
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    while True:
        if backend.poll() is not None or frontend.poll() is not None:
            stop()
        time.sleep(1)

if __name__ == "__main__":
    main()
