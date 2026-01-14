"""FastAPI application for Train-R cycling coach.

This is the main entry point for the Train-R API server.
It sets up the FastAPI application, configures middleware, and initializes services.
"""
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import AppConfig
from src.utils.logger import setup_logger
from src.integrations.llm_client import LLMClient
from src.integrations.intervals import IntervalsClient
from src.services.coach_service import CoachService
from src.services.data_sync import DataSyncService
from src.services.data_migrator import migrate_to_v2
from src.services.plan_uploader import PlanUploaderService
from src.api.routes import router
from src.api.websocket import manager

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


async def background_workout_upload(coach_service: CoachService, config: AppConfig):
    """Background task to upload pending workouts to intervals.icu.

    This task runs on application startup and uploads the next 2 weeks of workouts
    from the training plan to intervals.icu. Progress updates are broadcast to all
    connected WebSocket clients.

    Args:
        coach_service: Coach service with workout generator
        config: Application configuration
    """
    try:
        logger.info("Starting background workout upload...")

        # Create uploader service
        intervals_client = IntervalsClient(config.intervals_api_key, config)
        uploader = PlanUploaderService(
            workout_gen=coach_service.workout_generator,
            intervals_client=intervals_client,
            config=config
        )

        # Track progress for WebSocket broadcasts
        uploaded_count = 0
        total_count = 0

        # Progress callback sends WebSocket updates
        def progress_callback(workout_date: str, success: bool):
            """Called after each workout upload (sync function)."""
            nonlocal uploaded_count
            if success:
                uploaded_count += 1
                logger.info(f"Upload progress: {uploaded_count}/{total_count} - {workout_date}")

        # Upload next 2 weeks (14 workouts) in thread pool
        summary = await asyncio.wait_for(
            asyncio.to_thread(
                uploader.upload_pending_workouts,
                max_workouts=14,
                progress_callback=progress_callback
            ),
            timeout=300.0  # 5-minute timeout
        )

        # Extract total from summary
        total_count = summary.get("total", 0)

        logger.info(f"Background upload complete: {summary}")
        await manager.broadcast_upload_complete(summary)

    except asyncio.TimeoutError:
        logger.error("Background upload timed out after 5 minutes")
        await manager.broadcast_upload_error("Upload timed out after 5 minutes")
    except FileNotFoundError as e:
        logger.error(f"Training plan file not found: {e}")
        await manager.broadcast_upload_error(f"Plan file not found: {str(e)}")
    except Exception as e:
        logger.error(f"Background upload failed: {e}", exc_info=True)
        await manager.broadcast_upload_error(f"Upload failed: {str(e)}")


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

        # Flush LLM messages log file on startup
        llm_messages_log = _config.logs_dir / "llm_messages.json"
        if llm_messages_log.exists():
            llm_messages_log.unlink()
            logger.info("Flushed LLM messages log file")
        else:
            logger.info("LLM messages log file will be created on first LLM call")

        # Validate configuration
        _config.validate()
        logger.info("Configuration validated")

        # Initialize single shared LLM client with LangSmith tracing if configured
        llm_client = LLMClient(
            api_key=_config.llm_api_key,
            base_url=_config.llm_base_url,
            langsmith_tracing_enabled=_config.langsmith_tracing_enabled,
            langsmith_api_key=_config.langsmith_api_key,
            langsmith_project=_config.langsmith_project
        )
        logger.info(f"LLM client initialized: {_config.model_name}")

        # Initialize coach service (includes workout generation)
        _coach_service = CoachService(llm_client, _config)
        logger.info("Coach service initialized with tool support")

        # Migrate data structure to v2 if needed
        try:
            migrated = migrate_to_v2(_config)
            if migrated:
                logger.info("Data structure migrated to v2")
        except Exception as e:
            logger.warning(f"Data migration failed (continuing anyway): {e}")

        # Sync athlete data from intervals.icu on startup (includes power curves)
        try:
            intervals_client = IntervalsClient(
                api_key=_config.intervals_api_key,
                config=_config
            )
            sync_service = DataSyncService(intervals_client, _config)
            logger.info("Starting full data sync (including power curves)...")

            # Run synchronous sync in thread pool with timeout
            sync_result = await asyncio.wait_for(
                asyncio.to_thread(sync_service.sync_athlete_data),
                timeout=120.0
            )
            logger.info(f"Athlete data sync complete: {sync_result}")
        except asyncio.TimeoutError:
            logger.warning("Athlete data sync timed out after 120s, using existing data")
        except Exception as e:
            logger.error(f"Athlete data sync failed: {e}", exc_info=True)
            logger.info("Continuing with existing data if available")

        # Initialize current plan service and sync with intervals.icu data
        try:
            from src.services.current_plan_service import CurrentPlanService
            current_plan_service = CurrentPlanService(_config)

            # Load or initialize current plan from master
            current_plan = await asyncio.to_thread(current_plan_service.load_current_plan)
            logger.info(f"Current plan loaded with {len(current_plan.get('workouts', {}))} workouts")

            # Sync event_ids from intervals.icu data
            synced_count = await asyncio.to_thread(current_plan_service.sync_intervals_data)
            logger.info(f"Synced {synced_count} workouts with intervals.icu event IDs")
        except Exception as e:
            logger.error(f"Current plan initialization failed: {e}", exc_info=True)
            logger.info("Continuing without current plan (upload will fail if active_plan.json doesn't exist)")

        # Start background workout upload (non-blocking)
        upload_task = asyncio.create_task(
            background_workout_upload(_coach_service, _config)
        )
        # Store task reference for cleanup
        app.state.upload_task = upload_task
        logger.info("Background workout upload task started")

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

        # Close all WebSocket connections gracefully
        from src.api.websocket import manager
        await manager.close_all()

        logger.info("Shutdown complete")


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
