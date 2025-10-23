"""Development server for Train-R API.

This script runs the FastAPI server in development mode with hot reload enabled.
"""
import uvicorn
import sys
from pathlib import Path

# Add parent directory to path so we can import src module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Run the development server."""
    print("=" * 60)
    print("Train-R Development Server (Refactored Architecture)")
    print("=" * 60)
    print("API will be available at: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("Health check: http://localhost:8000/api/health")
    print("API docs: http://localhost:8000/docs")
    print("Press CTRL+C to stop")
    print("=" * 60)

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
