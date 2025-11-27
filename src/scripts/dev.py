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

from src.config import AppConfig

# Store processes so we can clean them up
processes = []

# Global config (set in main)
_config: AppConfig = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully with extended shutdown sequence."""
    print("\n\n" + "=" * 60)
    print("🛑 Shutting down Train-R Development Environment")
    print("=" * 60)
    print()

    # Step 1: Send SIGTERM to all processes
    print("Sending termination signal to servers...")
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()

    # Step 2: Wait with monitoring (5 second grace period)
    print("Waiting for graceful shutdown (5 seconds)...")
    start_time = time.time()
    while time.time() - start_time < 5:
        all_stopped = all(proc.poll() is not None for proc in processes)
        if all_stopped:
            elapsed = time.time() - start_time
            print(f"✅ All processes stopped gracefully ({elapsed:.1f}s)")
            break
        time.sleep(0.5)

    # Step 3: Force kill remaining processes
    remaining = [proc for proc in processes if proc.poll() is None]
    if remaining:
        print(f"⚠️  Force killing {len(remaining)} remaining process(es)...")
        for proc in remaining:
            proc.kill()
        time.sleep(0.5)

    # Step 4: Verify port release
    if _config:
        from src.utils.port_manager import is_port_available
        ports_to_check = [_config.backend_port, _config.frontend_port]

        print("\nVerifying port release...")
        for port in ports_to_check:
            if is_port_available(port):
                print(f"✅ Port {port}: Released")
            else:
                print(f"⚠️  Port {port}: Still in use (may take a moment)")

    print("\n" + "=" * 60)
    print("👋 Train-R stopped successfully")
    print("=" * 60)
    print()
    sys.exit(0)


def cleanup_development_ports(config: AppConfig) -> None:
    """Clean up ports before starting development servers.

    Automatically kills processes on configured ports and verifies availability.

    Args:
        config: Application configuration with port settings
    """
    from src.utils.port_manager import cleanup_ports, find_process_on_port

    ports = [config.backend_port, config.frontend_port]

    print("\n" + "="*60)
    print("🔍 Checking ports...")
    print("="*60 + "\n")

    # Find processes on ports
    found_processes = False
    for port in ports:
        proc_info = find_process_on_port(port)
        if proc_info:
            found_processes = True
            print(f"Port {port}: In use by PID {proc_info['pid']} ({proc_info['name']})")
            print(f"  Command: {proc_info['command']}")
            print(f"  Killing process...")

    if not found_processes:
        print("✅ All ports are available")
        print()
        return

    print()

    # Clean up all ports
    results = cleanup_ports(ports, timeout=3)

    # Verify and report
    print("Port cleanup results:")
    all_clear = True
    for port, success in results.items():
        if success:
            print(f"✅ Port {port}: Available")
        else:
            print(f"❌ Port {port}: Failed to clean up")
            all_clear = False

    if not all_clear:
        print("\n⚠️  Warning: Some ports could not be cleaned up")
        print("You may need to manually kill processes or check permissions")
        sys.exit(1)

    print()


def main():
    """Start both backend and frontend development servers."""
    global _config

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get project root (3 levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    frontend_dir = project_root / "frontend"

    # Load configuration
    from src.config import AppConfig
    _config = AppConfig.from_env()

    # Clean up ports before starting
    cleanup_development_ports(_config)

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
    print(f"Backend API:  http://localhost:{_config.backend_port}")
    print(f"API Docs:     http://localhost:{_config.backend_port}/docs")
    print(f"WebSocket:    ws://localhost:{_config.backend_port}/ws")
    print()
    print(f"Frontend:     http://localhost:{_config.frontend_port}")
    print()
    print("Press CTRL+C to stop all servers")
    print("=" * 60)
    print()

    # Start backend server
    print("Starting backend server...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.main:app", "--reload", "--host", _config.backend_host, "--port", str(_config.backend_port)],
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
