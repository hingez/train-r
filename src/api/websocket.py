"""WebSocket connection manager for real-time chat."""
import json
import logging
from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect

from src.api.schemas import AssistantMessage, ToolCall, ToolResult, DisplayUpdate, ErrorMessage, ConfirmationRequest

logger = logging.getLogger('train-r')


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store new WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection.

        Args:
            client_id: Unique client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, message: AssistantMessage | ToolCall | ToolResult | DisplayUpdate | ErrorMessage | ConfirmationRequest, client_id: str):
        """Send message to specific client.

        Args:
            message: Message to send
            client_id: Target client identifier
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message.model_dump(mode='json'))
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)

    async def send_assistant_message(self, content: str, client_id: str):
        """Send assistant message to client.

        Args:
            content: Message content
            client_id: Target client identifier
        """
        message = AssistantMessage(content=content)
        await self.send_message(message, client_id)

    async def send_tool_call(self, tool_name: str, tool_args: dict, client_id: str):
        """Send tool call notification to client.

        Args:
            tool_name: Name of tool being called
            tool_args: Tool arguments
            client_id: Target client identifier
        """
        message = ToolCall(tool_name=tool_name, tool_args=tool_args)
        await self.send_message(message, client_id)

    async def send_tool_result(self, tool_name: str, result: dict, success: bool, client_id: str):
        """Send tool result to client.

        Args:
            tool_name: Name of tool that was called
            result: Tool execution result
            success: Whether tool execution succeeded
            client_id: Target client identifier
        """
        message = ToolResult(tool_name=tool_name, result=result, success=success)
        await self.send_message(message, client_id)

    async def send_display_update(self, display_type: str, data: dict, client_id: str):
        """Send display update instruction to client.

        Args:
            display_type: Type of display to show
            data: Display data
            client_id: Target client identifier
        """
        message = DisplayUpdate(display_type=display_type, data=data)
        await self.send_message(message, client_id)

    async def send_error(self, error_message: str, client_id: str):
        """Send error message to client.

        Args:
            error_message: Error description
            client_id: Target client identifier
        """
        message = ErrorMessage(message=error_message)
        await self.send_message(message, client_id)

    async def send_confirmation_request(self, confirmation_id: str, question: str, context: dict, client_id: str):
        """Send confirmation request to client.

        Args:
            confirmation_id: Unique ID for this confirmation
            question: Question to ask the user
            context: Additional context for the confirmation
            client_id: Target client identifier
        """
        message = ConfirmationRequest(confirmation_id=confirmation_id, question=question, context=context)
        await self.send_message(message, client_id)

    async def close_all(self):
        """Close all active WebSocket connections gracefully.

        Called during application shutdown to ensure clean disconnect.
        """
        import asyncio

        logger.info(f"Closing {len(self.active_connections)} active WebSocket connections...")

        # Create list of close tasks
        close_tasks = []
        for client_id, websocket in list(self.active_connections.items()):
            try:
                # Send closing message
                close_tasks.append(websocket.close(code=1001, reason="Server shutting down"))
            except Exception as e:
                logger.error(f"Error closing connection {client_id}: {e}")

        # Wait for all closes with timeout
        if close_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*close_tasks, return_exceptions=True),
                    timeout=3.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some WebSocket connections did not close within timeout")

        # Clear the dictionary
        self.active_connections.clear()
        logger.info("All WebSocket connections closed")


# Global connection manager instance
manager = ConnectionManager()
