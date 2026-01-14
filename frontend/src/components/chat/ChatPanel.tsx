import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ChatMessage } from "./ChatMessage";
import { ConfirmationDialog } from "./ConfirmationDialog";
import { CyclingLoadingSpinner } from "@/components/ui/cycling-loading-spinner";
import type { Message, ConfirmationResponse } from "@/types/messages";
import { Send, Bot, Sparkles } from "lucide-react";

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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
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

  // Filter out display updates and completed tool_call messages
  const toolResults = messages.filter(m => m.type === "tool_result");
  const completedToolNames = new Set(
    toolResults.map(m => m.type === "tool_result" ? m.tool_name : null).filter(Boolean)
  );

  const chatMessages = messages.filter(m => {
    if (m.type === "display_update") return false;
    // Hide tool_call if its corresponding tool_result exists
    if (m.type === "tool_call" && completedToolNames.has(m.tool_name)) {
      return false;
    }
    return true;
  });

  const pendingConfirmation = messages.find(
    m => m.type === "confirmation_request"
  ) as Message & { type: "confirmation_request" } | undefined;

  const isWaitingForResponse = () => {
    if (chatMessages.length === 0) return false;
    const lastMessage = chatMessages[chatMessages.length - 1];
    if (lastMessage.type === "user_message") return true;
    if (lastMessage.type === "tool_call") return true;
    return false;
  };

  return (
    <div className="flex flex-col h-full bg-card-light dark:bg-card-dark border-l border-gray-200 dark:border-gray-700 shadow-xl z-20">
      {/* Header */}
      <div className="border-b border-gray-100 dark:border-gray-700 p-4 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-purple-400 flex items-center justify-center text-white font-bold shadow-lg">
              <Bot className="w-5 h-5" />
            </div>
            <div className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white dark:border-gray-800 ${connectionStatus === 'connected' ? 'bg-green-500' : 'bg-gray-400'}`}></div>
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-tight text-text-light dark:text-text-dark">Train-R Coach</h2>
            <p className="text-[10px] text-subtext-light dark:text-subtext-dark font-medium uppercase tracking-wider">AI Assistant</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-background-light/50 dark:bg-background-dark/50">
        {chatMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3 opacity-60">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
              <Sparkles className="w-6 h-6" />
            </div>
            <p className="text-sm text-subtext-light dark:text-subtext-dark">
              Ready to help you crush your goals. Ask me to analyze your data or build a plan!
            </p>
          </div>
        )}

        {chatMessages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}

        {pendingConfirmation && (
          <div className="mt-4 animate-in fade-in slide-in-from-bottom-2">
            <ConfirmationDialog
              question={pendingConfirmation.question}
              context={pendingConfirmation.context}
              onConfirm={() => handleConfirmation(pendingConfirmation.confirmation_id, true)}
              onReject={() => handleConfirmation(pendingConfirmation.confirmation_id, false)}
            />
          </div>
        )}

        {isWaitingForResponse() && (
          <div className="flex justify-start animate-in fade-in slide-in-from-bottom-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-100 dark:border-gray-700">
              <CyclingLoadingSpinner />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-card-light dark:bg-card-dark border-t border-gray-100 dark:border-gray-700">
        <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about workouts..."
            disabled={connectionStatus !== "connected"}
            className="w-full bg-gray-100 dark:bg-gray-800 border-0 rounded-full py-3 px-4 pl-4 pr-12 text-sm text-text-light dark:text-text-dark placeholder-subtext-light dark:placeholder-subtext-dark focus:ring-2 focus:ring-primary focus:bg-white dark:focus:bg-gray-900 transition-all shadow-inner"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || connectionStatus !== "connected"}
            className="absolute right-1.5 top-1.5 h-8 w-8 rounded-full bg-primary hover:bg-primary-dark text-white shadow-md transition-transform active:scale-95"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
