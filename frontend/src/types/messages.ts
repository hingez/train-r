export type MessageType =
  | "user_message"
  | "assistant_message"
  | "tool_call"
  | "tool_result"
  | "display_update"
  | "confirmation_request"
  | "confirmation_response"
  | "error"
  | "upload_progress"
  | "upload_complete"
  | "upload_error";

export type DisplayType = "welcome" | "workout" | "charts" | "tool_execution" | "training_plan" | "dashboard" | "loading";

export interface BaseMessage {
  type: MessageType;
  timestamp?: string;
}

export interface UserMessage extends BaseMessage {
  type: "user_message";
  content: string;
}

export interface AssistantMessage extends BaseMessage {
  type: "assistant_message";
  content: string;
}

export interface ToolCall extends BaseMessage {
  type: "tool_call";
  tool_name: string;
  tool_args: Record<string, any>;
}

export interface ToolResult extends BaseMessage {
  type: "tool_result";
  tool_name: string;
  result: Record<string, any>;
  success: boolean;
}

export interface DisplayUpdate extends BaseMessage {
  type: "display_update";
  display_type: DisplayType;
  data?: Record<string, any>;
}

export interface ErrorMessage extends BaseMessage {
  type: "error";
  message: string;
}

export interface ConfirmationRequest extends BaseMessage {
  type: "confirmation_request";
  confirmation_id: string;
  question: string;
  context?: Record<string, any>;
}

export interface ConfirmationResponse extends BaseMessage {
  type: "confirmation_response";
  confirmation_id: string;
  confirmed: boolean;
}

export interface UploadProgressMessage extends BaseMessage {
  type: "upload_progress";
  current: number;
  total: number;
  workout_date: string;
}

export interface UploadCompleteMessage extends BaseMessage {
  type: "upload_complete";
  summary: {
    success: number;
    skipped: number;
    failed: number;
    total: number;
  };
}

export interface UploadErrorMessage extends BaseMessage {
  type: "upload_error";
  error: string;
}

export type Message =
  | UserMessage
  | AssistantMessage
  | ToolCall
  | ToolResult
  | DisplayUpdate
  | ConfirmationRequest
  | ConfirmationResponse
  | ErrorMessage
  | UploadProgressMessage
  | UploadCompleteMessage
  | UploadErrorMessage;
