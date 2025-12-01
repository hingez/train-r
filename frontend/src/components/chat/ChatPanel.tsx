import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ChatMessage } from "./ChatMessage";
import { ConfirmationDialog } from "./ConfirmationDialog";
import type { Message, ConfirmationResponse } from "@/types/messages";
import { Send } from "lucide-react";

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  onSendConfirmation: (response: ConfirmationResponse) => void;
  connectionStatus: string;
}

export function ChatPanel({ messages, onSendMessage, onSendConfirmation, connectionStatus }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && connectionStatus === "connected") {
      onSendMessage(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter, new line on Shift+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && connectionStatus === "connected") {
        onSendMessage(input.trim());
        setInput("");
      }
    }
  };

  const handleConfirmation = (confirmationId: string, confirmed: boolean) => {
    onSendConfirmation({
      type: "confirmation_response",
      confirmation_id: confirmationId,
      confirmed,
    });
  };

  // Filter out display_update messages from chat view and find pending confirmations
  const chatMessages = messages.filter(m => m.type !== "display_update");
  const pendingConfirmation = messages.find(
    m => m.type === "confirmation_request"
  ) as Message & { type: "confirmation_request" } | undefined;

  return (
    <div className="flex flex-col h-screen bg-background border-l">
      {/* Header */}
      <div className="border-b px-4 py-3">
        <h2 className="font-semibold">Train-R Coach</h2>
        <p className="text-xs text-muted-foreground">
          {connectionStatus === "connected" && "Connected"}
          {connectionStatus === "connecting" && "Connecting..."}
          {connectionStatus === "disconnected" && "Disconnected"}
          {connectionStatus === "error" && "Connection Error"}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {chatMessages.length === 0 && (
          <div className="text-center text-muted-foreground text-sm mt-8">
            Send a message to start chatting with your cycling coach!
          </div>
        )}
        {chatMessages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}

        {/* Show confirmation dialog if there's a pending confirmation */}
        {pendingConfirmation && (
          <div className="mt-4">
            <ConfirmationDialog
              question={pendingConfirmation.question}
              context={pendingConfirmation.context}
              onConfirm={() => handleConfirmation(pendingConfirmation.confirmation_id, true)}
              onReject={() => handleConfirmation(pendingConfirmation.confirmation_id, false)}
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t px-4 py-4">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about workouts, training plans... (Enter to send, Shift+Enter for new line)"
            disabled={connectionStatus !== "connected"}
            className="flex-1 min-h-12 max-h-32 resize-none"
          />
          <Button
            type="submit"
            disabled={!input.trim() || connectionStatus !== "connected"}
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
