"""Development environment launcher for Train-R.

This script starts both the backend API server and the frontend development server,
making it easy to run the full stack with a single command.
"""
import subprocess
import sys
import signal
import time
import os
from pathlib import Path

from src.config import BACKEND_HOST, BACKEND_PORT, FRONTEND_PORT

# Store processes so we can clean them up
processes = []


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully by terminating all child processes."""
    print("\n\n" + "=" * 60)
    print("Shutting down Train-R development environment...")
    print("=" * 60)

    for proc in processes:
        if proc.poll() is None:  # Process still running
            proc.terminate()

    # Give processes time to terminate gracefully
    time.sleep(1)

    # Force kill if still running
    for proc in processes:
        if proc.poll() is None:
            proc.kill()

    print("All processes terminated. Goodbye!")
    sys.exit(0)


def main():
    """Start both backend and frontend development servers."""
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get project root (3 levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    frontend_dir = project_root / "frontend"

    # Check if frontend directory exists
    if not frontend_dir.exists():
        print("ERROR: Frontend directory not found at:", frontend_dir)
        print("Please ensure the frontend is set up before running this command.")
        sys.exit(1)

    # Check if node_modules exists
    if not (frontend_dir / "node_modules").exists():
        print("=" * 60)
        print("Installing frontend dependencies...")
        print("=" * 60)
        install_proc = subprocess.run(
            ["npm", "install"],
            cwd=str(frontend_dir)
        )
        if install_proc.returncode != 0:
            print("ERROR: Failed to install frontend dependencies")
            sys.exit(1)

    print("=" * 60)
    print("🚀 Starting Train-R Development Environment")
    print("=" * 60)
    print()
    print(f"Backend API:  http://localhost:{BACKEND_PORT}")
    print(f"API Docs:     http://localhost:{BACKEND_PORT}/docs")
    print(f"WebSocket:    ws://localhost:{BACKEND_PORT}/ws")
    print()
    print(f"Frontend:     http://localhost:{FRONTEND_PORT}")
    print()
    print("Press CTRL+C to stop all servers")
    print("=" * 60)
    print()

    # Start backend server
    print("Starting backend server...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--reload", "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(backend_proc)

    # Give backend a moment to start
    time.sleep(2)

    # Start frontend server
    print("Starting frontend server...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(frontend_proc)

    print()
    print("=" * 60)
    print("✅ Both servers are starting up...")
    print("=" * 60)
    print()

    # Monitor processes and output logs
    try:
        while True:
            # Check if any process has died
            for proc in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️  A process has stopped unexpectedly (exit code: {proc.returncode})")
                    signal_handler(None, None)

            # Read output from processes (non-blocking)
            for proc in processes:
                try:
                    line = proc.stdout.readline()
                    if line:
                        print(line.strip())
                except:
                    pass

            time.sleep(0.1)

    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
