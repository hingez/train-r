"""API routes for Train-R.

This module contains all API endpoints including WebSocket routes.
"""
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.websocket import manager
from src.api.schemas import UserMessage, ConfirmationResponse
from src.services.dashboard_service import DashboardService

logger = logging.getLogger('train-r')

# Create API router
router = APIRouter()

# Store pending confirmations per client
# Format: {client_id: {confirmation_id: {action_data}}}
pending_confirmations: Dict[str, Dict[str, Dict[str, Any]]] = {}


@router.get("/api/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status dictionary
    """
    from src.config import APP_VERSION
    return {
        "status": "healthy",
        "service": "train-r-api",
        "version": APP_VERSION
    }


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat.

    This endpoint manages the conversation loop with the cycling coach,
    handling tool execution and display updates.

    Args:
        websocket: WebSocket connection
    """
    from src.main import get_coach_service

    # Get the global coach service instance
    coach_service = get_coach_service()

    # Generate unique client ID
    client_id = str(uuid.uuid4())

    # Accept connection
    await manager.connect(websocket, client_id)

    try:
        # Send loading screen first
        await manager.send_display_update(
            display_type="loading",
            data={"message": "Refreshing workouts from intervals.icu..."},
            client_id=client_id
        )

        # Sync athlete data on every page refresh
        try:
            from src.integrations.intervals import IntervalsClient
            from src.services.data_sync import DataSyncService
            import asyncio

            intervals_client = IntervalsClient(
                api_key=coach_service.config.intervals_api_key,
                config=coach_service.config
            )
            sync_service = DataSyncService(intervals_client, coach_service.config)

            # Run sync in thread pool with timeout (skip power curves for speed)
            sync_result = await asyncio.wait_for(
                asyncio.to_thread(sync_service.sync_athlete_data, skip_power_curves=True),
                timeout=30.0
            )
            logger.info(f"Data sync complete for client {client_id[:8]}: {sync_result}")

        except asyncio.TimeoutError:
            logger.warning(f"Data sync timed out for client {client_id[:8]}, using existing data")
        except Exception as e:
            logger.error(f"Data sync failed for client {client_id[:8]}: {e}", exc_info=True)

        # Send dashboard data automatically (replaces welcome screen)
        try:
            dashboard_service = DashboardService(coach_service.config)
            dashboard_data = dashboard_service.get_dashboard_data()

            await manager.send_display_update(
                display_type="dashboard",
                data=dashboard_data,
                client_id=client_id
            )
            logger.info(f"Dashboard data sent to client {client_id[:8]}")
        except Exception as e:
            logger.error(f"Error sending dashboard data: {e}", exc_info=True)
            # Fallback to welcome screen if dashboard fails
            await manager.send_display_update(
                display_type="welcome",
                data={"message": "Welcome to Train-R!"},
                client_id=client_id
            )

        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            try:
                # Check if this is a confirmation response
                if data.get("type") == "confirmation_response":
                    confirmation = ConfirmationResponse(**data)
                    logger.info(f"Received confirmation from {client_id}: {confirmation.confirmed}")

                    # Handle the confirmation
                    if client_id in pending_confirmations and confirmation.confirmation_id in pending_confirmations[client_id]:
                        action_data = pending_confirmations[client_id][confirmation.confirmation_id]

                        # Handle training plan upload
                        if action_data.get("action") == "upload_training_plan":
                            if confirmation.confirmed:
                                # TODO: Future implementation - bulk upload to intervals.icu
                                await manager.send_assistant_message(
                                    "Uploading workouts to intervals.icu... (Feature coming soon!)",
                                    client_id
                                )
                            else:
                                await manager.send_assistant_message(
                                    "Plan created but not uploaded. You can view and manage it here.",
                                    client_id
                                )

                        # Handle single workout upload
                        else:
                            if confirmation.confirmed:
                                # User confirmed - save and upload the workout
                                from src.integrations.intervals import IntervalsClient
                                from src.main import get_coach_service

                                coach_service = get_coach_service()

                                try:
                                    # Save the workout first
                                    filepath = coach_service.workout_generator.save_workout(
                                        action_data["zwo_content"],
                                        action_data.get("workout_name", "workout")
                                    )
                                    logger.info(f"Workout saved to: {filepath}")

                                    # Upload to intervals.icu
                                    intervals_client = IntervalsClient(
                                        api_key=coach_service.config.intervals_api_key,
                                        config=coach_service.config
                                    )

                                    response = intervals_client.upload_workout(
                                        file_path=filepath,
                                        start_date=action_data["scheduled_time"],
                                        external_id=action_data["external_id"]
                                    )

                                    logger.info(f"Upload successful - Event ID: {response.get('id')}")

                                    # Send success message
                                    await manager.send_assistant_message(
                                        f"Workout saved and uploaded successfully to intervals.icu! Scheduled for {action_data['scheduled_time']}",
                                        client_id
                                    )

                                except Exception as e:
                                    logger.error(f"Error saving/uploading workout: {str(e)}", exc_info=True)
                                    await manager.send_error(f"Failed to save/upload workout: {str(e)}", client_id)

                            else:
                                # User rejected - send rejection message without saving
                                await manager.send_assistant_message(
                                    "Workout not saved or sent to intervals.icu as requested.",
                                    client_id
                                )

                        # Clean up the pending confirmation
                        del pending_confirmations[client_id][confirmation.confirmation_id]
                        if not pending_confirmations[client_id]:
                            del pending_confirmations[client_id]

                    continue

                # Parse user message
                user_msg = UserMessage(**data)

                # Generate request ID for correlation
                request_id = str(uuid.uuid4())[:8]  # Short UUID for readability
                logger.info(f"[client={client_id[:8]}] [req={request_id}] Received: {user_msg.content[:100]}")

                # Define callbacks for tool execution
                async def on_tool_call(tool_name: str, tool_args: dict):
                    """Callback when tool is called."""
                    await manager.send_tool_call(tool_name, tool_args, client_id)
                    # Update display to show tool execution
                    await manager.send_display_update(
                        display_type="tool_execution",
                        data={
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "status": "executing"
                        },
                        client_id=client_id
                    )

                async def on_tool_result(tool_name: str, result: dict, success: bool):
                    """Callback when tool execution completes."""
                    await manager.send_tool_result(tool_name, result, success, client_id)

                    # Update display based on tool result
                    if tool_name == "create_one_off_workout" and success:
                        # Generate confirmation ID
                        confirmation_id = str(uuid.uuid4())

                        # Store the action data for later
                        if client_id not in pending_confirmations:
                            pending_confirmations[client_id] = {}

                        pending_confirmations[client_id][confirmation_id] = {
                            "zwo_content": result.get("zwo_content"),
                            "filename": result.get("filename"),
                            "workout_name": result.get("workout_name"),
                            "workout_description": result.get("workout_description"),
                            "scheduled_time": result.get("scheduled_time"),
                            "external_id": result.get("external_id")
                        }

                        # Send confirmation request to user
                        await manager.send_confirmation_request(
                            confirmation_id=confirmation_id,
                            question="Send to intervals.icu?",
                            context={
                                "Workout": result.get("workout_name"),
                                "Scheduled Time": result.get("scheduled_time")
                            },
                            client_id=client_id
                        )

                        # Show workout visualization
                        await manager.send_display_update(
                            display_type="workout",
                            data={
                                "workout_name": result.get("workout_name"),
                                "workout_description": result.get("workout_description"),
                                "scheduled_time": result.get("scheduled_time"),
                                "workout_data": result.get("workout_data"),
                                "workout_file": result.get("filename")
                            },
                            client_id=client_id
                        )

                    # Handle training plan creation
                    if tool_name == "create_workout_plan" and success:
                        # Send display update for plan visualization
                        await manager.send_display_update(
                            display_type="training_plan",
                            data={
                                "plan": result.get("plan"),
                                "summarized": result.get("summarized"),
                                "total_weeks": result.get("total_weeks"),
                                "total_workouts": result.get("total_workouts")
                            },
                            client_id=client_id
                        )

                        # Send confirmation request for uploading workouts
                        confirmation_id = str(uuid.uuid4())

                        if client_id not in pending_confirmations:
                            pending_confirmations[client_id] = {}

                        pending_confirmations[client_id][confirmation_id] = {
                            "action": "upload_training_plan",
                            "plan_data": result.get("plan"),
                            "summarized_data": result.get("summarized")
                        }

                        await manager.send_confirmation_request(
                            confirmation_id=confirmation_id,
                            question=f"Upload all {result.get('total_workouts', 168)} workouts to intervals.icu?",
                            context={
                                "total_weeks": result.get("total_weeks"),
                                "total_workouts": result.get("total_workouts")
                            },
                            client_id=client_id
                        )

                # Process message through coach service
                # Pass client_id as session_id for LangSmith thread grouping
                response = await coach_service.process_message(
                    user_msg.content,
                    request_id=request_id,
                    session_id=client_id,
                    on_tool_call=on_tool_call,
                    on_tool_result=on_tool_result
                )

                # Send assistant response
                await manager.send_assistant_message(response, client_id)

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await manager.send_error(f"Error processing message: {str(e)}", client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(client_id)
