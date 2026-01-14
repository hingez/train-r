"""Pydantic models for API messages and responses."""
from typing import Optional, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Base chat message structure."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class UserMessage(BaseModel):
    """User message from frontend."""
    type: Literal["user_message"] = "user_message"
    content: str


class AssistantMessage(BaseModel):
    """Assistant response to frontend."""
    type: Literal["assistant_message"] = "assistant_message"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolCall(BaseModel):
    """Tool call notification."""
    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    tool_args: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolResult(BaseModel):
    """Tool execution result."""
    type: Literal["tool_result"] = "tool_result"
    tool_name: str
    result: dict[str, Any]
    success: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class DisplayUpdate(BaseModel):
    """Display panel update instruction."""
    type: Literal["display_update"] = "display_update"
    display_type: Literal["welcome", "workout", "charts", "tool_execution", "training_plan", "dashboard", "loading"]
    data: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorMessage(BaseModel):
    """Error notification."""
    type: Literal["error"] = "error"
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfirmationRequest(BaseModel):
    """Request user confirmation for an action."""
    type: Literal["confirmation_request"] = "confirmation_request"
    confirmation_id: str
    question: str
    context: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConfirmationResponse(BaseModel):
    """User's response to a confirmation request."""
    type: Literal["confirmation_response"] = "confirmation_response"
    confirmation_id: str
    confirmed: bool


class UploadProgress(BaseModel):
    """Upload progress notification."""
    type: Literal["upload_progress"] = "upload_progress"
    current: int
    total: int
    workout_date: str
    timestamp: datetime = Field(default_factory=datetime.now)


class UploadComplete(BaseModel):
    """Upload completion notification."""
    type: Literal["upload_complete"] = "upload_complete"
    summary: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class UploadError(BaseModel):
    """Upload error notification."""
    type: Literal["upload_error"] = "upload_error"
    error: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConnectionStatus(BaseModel):
    """WebSocket connection status."""
    connected: bool
    message: Optional[str] = None
