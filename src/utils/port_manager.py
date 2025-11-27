"""Port management utilities for development environment.

This module provides cross-platform utilities for managing ports including:
- Finding processes using specific ports
- Killing processes on ports (graceful and force)
- Verifying port availability
- Bulk port cleanup operations
"""
import os
import sys
import time
import socket
import logging
import subprocess
from typing import Optional, Dict, List

logger = logging.getLogger('train-r')


def find_process_on_port(port: int) -> Optional[Dict[str, str]]:
    """Find process using specified port.

    Args:
        port: Port number to check

    Returns:
        Dict with 'pid', 'name', 'command' keys if port is in use, None if free

    Raises:
        RuntimeError: If unable to check port status
    """
    try:
        if sys.platform == 'win32':
            return _find_process_windows(port)
        else:
            return _find_process_unix(port)
    except Exception as e:
        logger.error(f"Error finding process on port {port}: {e}")
        raise RuntimeError(f"Failed to check port {port}: {e}")


def _find_process_unix(port: int) -> Optional[Dict[str, str]]:
    """Find process on Unix/macOS using lsof.

    Args:
        port: Port number to check

    Returns:
        Process info dict or None if port is free
    """
    try:
        # Use lsof to find process using the port
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None

        # Get the PID
        pid = result.stdout.strip().split('\n')[0]

        # Get process name and command
        try:
            ps_result = subprocess.run(
                ['ps', '-p', pid, '-o', 'comm=,args='],
                capture_output=True,
                text=True,
                timeout=5
            )

            if ps_result.returncode == 0:
                output = ps_result.stdout.strip()
                parts = output.split(None, 1)
                name = parts[0] if parts else 'unknown'
                command = parts[1] if len(parts) > 1 else name

                return {
                    'pid': pid,
                    'name': name,
                    'command': command
                }
        except Exception:
            pass

        # Fallback if ps fails
        return {
            'pid': pid,
            'name': 'unknown',
            'command': 'unknown'
        }

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout checking port {port}")
        return None
    except FileNotFoundError:
        logger.error("lsof command not found")
        return None
    except Exception as e:
        logger.debug(f"Error finding process on port {port}: {e}")
        return None


def _find_process_windows(port: int) -> Optional[Dict[str, str]]:
    """Find process on Windows using netstat.

    Args:
        port: Port number to check

    Returns:
        Process info dict or None if port is free
    """
    try:
        # Use netstat to find process
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return None

        # Parse netstat output
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                pid = parts[-1]

                # Get process name using tasklist
                try:
                    tasklist_result = subprocess.run(
                        ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if tasklist_result.returncode == 0:
                        # Parse CSV output
                        csv_line = tasklist_result.stdout.strip().strip('"')
                        name = csv_line.split('","')[0].strip('"')

                        return {
                            'pid': pid,
                            'name': name,
                            'command': name
                        }
                except Exception:
                    pass

                # Fallback
                return {
                    'pid': pid,
                    'name': 'unknown',
                    'command': 'unknown'
                }

        return None

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout checking port {port}")
        return None
    except FileNotFoundError:
        logger.error("netstat command not found")
        return None
    except Exception as e:
        logger.debug(f"Error finding process on port {port}: {e}")
        return None


def kill_process_on_port(port: int, force: bool = False) -> bool:
    """Kill process on specified port.

    Args:
        port: Port number
        force: If True, use SIGKILL immediately. If False, try SIGTERM first.

    Returns:
        True if successful, False otherwise
    """
    proc_info = find_process_on_port(port)

    if not proc_info:
        logger.debug(f"No process found on port {port}")
        return True

    pid = int(proc_info['pid'])

    try:
        if sys.platform == 'win32':
            # Windows: use taskkill
            if force:
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True, capture_output=True)
            else:
                subprocess.run(['taskkill', '/PID', str(pid)], check=True, capture_output=True)
        else:
            # Unix/macOS: use signals
            import signal
            if force:
                os.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGTERM)

        logger.info(f"Killed process {pid} on port {port}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to kill process {pid}: {e}")
        return False
    except ProcessLookupError:
        logger.debug(f"Process {pid} already terminated")
        return True
    except PermissionError:
        logger.error(f"Permission denied to kill process {pid}")
        return False
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False


def is_port_available(port: int) -> bool:
    """Check if port is available using socket binding test.

    Args:
        port: Port number to check

    Returns:
        True if port is available, False if in use
    """
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', port))
        return True
    except OSError:
        return False
    finally:
        if sock:
            sock.close()


def cleanup_ports(ports: List[int], timeout: int = 3) -> Dict[int, bool]:
    """Clean up multiple ports with graceful shutdown.

    Process: SIGTERM → wait timeout → SIGKILL if needed

    Args:
        ports: List of ports to clean up
        timeout: Seconds to wait for graceful shutdown before force killing

    Returns:
        Dict mapping port to success status (True if cleaned up or already free)
    """
    results = {}

    # Step 1: Send SIGTERM to all processes
    processes_to_kill = {}
    for port in ports:
        proc_info = find_process_on_port(port)
        if proc_info:
            processes_to_kill[port] = proc_info
            # Try graceful kill
            kill_process_on_port(port, force=False)
        else:
            # Port already free
            results[port] = True

    if not processes_to_kill:
        return results

    # Step 2: Wait for graceful shutdown
    logger.info(f"Waiting {timeout}s for processes to terminate gracefully...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check which ports are now free
        for port in list(processes_to_kill.keys()):
            if is_port_available(port):
                results[port] = True
                del processes_to_kill[port]

        if not processes_to_kill:
            # All ports freed
            break

        time.sleep(0.5)

    # Step 3: Force kill remaining processes
    if processes_to_kill:
        logger.warning(f"Force killing {len(processes_to_kill)} remaining process(es)")
        for port in list(processes_to_kill.keys()):
            success = kill_process_on_port(port, force=True)
            if success:
                # Wait briefly and verify
                time.sleep(0.5)
                results[port] = is_port_available(port)
            else:
                results[port] = False

    return results
