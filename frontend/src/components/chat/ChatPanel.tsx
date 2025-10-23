import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatMessage } from "./ChatMessage";
import type { Message } from "@/types/messages";
import { Send } from "lucide-react";

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  connectionStatus: string;
}

export function ChatPanel({ messages, onSendMessage, connectionStatus }: ChatPanelProps) {
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

  // Filter out display_update messages from chat view
  const chatMessages = messages.filter(m => m.type !== "display_update");

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
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t px-4 py-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about workouts, training plans..."
            disabled={connectionStatus !== "connected"}
            className="flex-1"
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
