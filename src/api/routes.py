"""API routes for Train-R.

This module contains all API endpoints including WebSocket routes.
"""
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.websocket import manager
from src.api.schemas import UserMessage

logger = logging.getLogger('train-r')

# Create API router
router = APIRouter()


@router.get("/api/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status dictionary
    """
    return {
        "status": "healthy",
        "service": "train-r-api",
        "version": "0.2.0"  # Updated version for refactored structure
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
        # Send welcome message
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
                # Parse user message
                user_msg = UserMessage(**data)
                logger.info(f"Received from {client_id}: {user_msg.content}")

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
                        # Show workout visualization
                        await manager.send_display_update(
                            display_type="workout",
                            data={
                                "workout_file": result.get("workout_file"),
                                "scheduled_time": result.get("scheduled_time")
                            },
                            client_id=client_id
                        )

                # Process message through coach service
                response = await coach_service.process_message(
                    user_msg.content,
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
