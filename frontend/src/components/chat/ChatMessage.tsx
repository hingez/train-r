import { cn } from "@/lib/utils";
import type { Message } from "@/types/messages";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  if (message.type === "user_message") {
    return (
      <div className="flex justify-end mb-4">
        <div className="bg-primary text-primary-foreground rounded-lg px-4 py-2 max-w-[80%]">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.type === "assistant_message") {
    return (
      <div className="flex justify-start mb-4">
        <div className="bg-muted rounded-lg px-4 py-2 max-w-[80%]">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.type === "tool_call") {
    return (
      <div className="flex justify-center mb-4">
        <div className="bg-accent text-accent-foreground rounded-lg px-3 py-1 text-xs">
          Executing: {message.tool_name}
        </div>
      </div>
    );
  }

  if (message.type === "tool_result") {
    return (
      <div className="flex justify-center mb-4">
        <div
          className={cn(
            "rounded-lg px-3 py-1 text-xs",
            message.success ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
          )}
        >
          {message.success ? "✓" : "✗"} {message.tool_name} completed
        </div>
      </div>
    );
  }

  if (message.type === "error") {
    return (
      <div className="flex justify-center mb-4">
        <div className="bg-destructive text-destructive-foreground rounded-lg px-3 py-2 text-sm">
          Error: {message.message}
        </div>
      </div>
    );
  }

  return null;
}
