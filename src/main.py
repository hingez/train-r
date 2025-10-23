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
from src.models.gemini_client import GeminiClient
from src.services.coach_service import CoachService
from src.services.workout_service import WorkoutService
from src.api.routes import router

# Initialize logging
logger = setup_logger()

# Global service instances
_coach_service: Optional[CoachService] = None
_workout_service: Optional[WorkoutService] = None


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


def get_workout_service() -> WorkoutService:
    """Get the global workout service instance.

    Returns:
        WorkoutService instance

    Raises:
        RuntimeError: If service not initialized (app not started)
    """
    if _workout_service is None:
        raise RuntimeError("Workout service not initialized. App may not have started.")
    return _workout_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown tasks for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    global _coach_service, _workout_service

    # Startup
    logger.info("=" * 60)
    logger.info("Starting Train-R API Server (Refactored Architecture)")
    logger.info("=" * 60)

    try:
        # Load configuration from environment
        config = AppConfig.from_env()
        logger.info("Configuration loaded successfully")

        # Configure CORS with settings from config
        configure_cors(config)

        # Create required directories
        config.create_directories()

        # Validate configuration
        config.validate()
        logger.info("Configuration validated")

        # Initialize single shared LLM client
        llm_client = GeminiClient(api_key=config.gemini_api_key)
        logger.info(f"LLM client initialized: {config.model_name}")

        # Initialize workout service first (needed by coach service)
        _workout_service = WorkoutService(llm_client, config)
        logger.info("Workout service initialized")

        # Initialize coach service with workout service
        _coach_service = CoachService(llm_client, config, _workout_service)
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
    version="0.2.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(router)

logger.info("FastAPI application created and configured")


def configure_cors(config: AppConfig):
    """Configure CORS middleware using app configuration.

    Args:
        config: Application configuration with CORS settings
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS configured for origins: {', '.join(config.cors_origins)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
