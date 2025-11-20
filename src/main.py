"""FastAPI application for Train-R cycling coach.

This is the main entry point for the Train-R API server.
It sets up the FastAPI application, configures middleware, and initializes services.
"""
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import AppConfig
from src.utils.logger import setup_logger
from src.integrations.llm_client import LLMClient
from src.services.coach_service import CoachService
from src.api.routes import router

# Initialize logging
logger = setup_logger()

# Load configuration early for CORS setup
_config = AppConfig.from_env()

# Global service instance
_coach_service: Optional[CoachService] = None


def get_coach_service() -> CoachService:
    """Get the global coach service instance.

    Returns:
        CoachService instance

    Raises:
        RuntimeError: If service not initialized (app not started)
    """
    if _coach_service is None:
        raise RuntimeError("Coach service not initialized. App may not have started.")
    return _coach_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown tasks for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    global _coach_service

    # Startup
    logger.info("=" * 60)
    logger.info("Starting Train-R API Server (Refactored Architecture)")
    logger.info("=" * 60)

    try:
        # Create required directories
        _config.create_directories()

        # Validate configuration
        _config.validate()
        logger.info("Configuration validated")

        # Initialize single shared LLM client
        llm_client = LLMClient(api_key=_config.llm_api_key, base_url=_config.llm_base_url)
        logger.info(f"LLM client initialized: {_config.model_name}")

        # Initialize coach service (includes workout generation)
        _coach_service = CoachService(llm_client, _config)
        logger.info("Coach service initialized with tool support")

        logger.info("=" * 60)
        logger.info("Train-R API Server ready")
        logger.info("=" * 60)

        yield

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise

    finally:
        # Shutdown
        logger.info("=" * 60)
        logger.info("Shutting down Train-R API Server")
        logger.info("=" * 60)


# Create FastAPI app
app = FastAPI(
    title="Train-R API",
    description="LLM-powered cycling coach API with WebSocket support (Refactored)",
    version=_config.app_version,
    lifespan=lifespan
)

# Configure CORS middleware (must be done before app starts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS configured for origins: {', '.join(_config.cors_origins)}")

# Include API routes
app.include_router(router)

logger.info("FastAPI application created and configured")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=_config.backend_host, port=_config.backend_port)
