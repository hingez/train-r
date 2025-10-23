export type MessageType =
  | "user_message"
  | "assistant_message"
  | "tool_call"
  | "tool_result"
  | "display_update"
  | "error";

export type DisplayType = "welcome" | "workout" | "charts" | "tool_execution";

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

export type Message =
  | UserMessage
  | AssistantMessage
  | ToolCall
  | ToolResult
  | DisplayUpdate
  | ErrorMessage;
