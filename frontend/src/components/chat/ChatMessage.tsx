import { cn } from "@/lib/utils";
import { getToolAlias } from "@/lib/toolAliases";
import type { Message } from "@/types/messages";
import { Wrench } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useState, useEffect } from "react";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  if (message.type === "user_message") {
    return (
      <div className="flex justify-end mb-4 animate-in fade-in slide-in-from-bottom-2">
        <div className="bg-primary hover:bg-primary-dark transition-colors text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[85%] shadow-md border border-primary/20">
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.type === "assistant_message") {
    return (
      <div className="flex justify-start mb-4 animate-in fade-in slide-in-from-bottom-2">
        <div className="bg-white dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[85%] shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="text-sm text-text-light dark:text-text-dark leading-relaxed prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                code: ({ children }) => <code className="bg-gray-100 dark:bg-gray-900 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                pre: ({ children }) => <pre className="bg-gray-100 dark:bg-gray-900 p-2 rounded overflow-x-auto mb-2">{children}</pre>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  if (message.type === "tool_call") {
    return (
      <div className="flex justify-center mb-4 animate-in fade-in">
        <div className="flex items-center gap-2 bg-gray-100/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-full px-4 py-1.5 backdrop-blur-sm">
          <div className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></div>
          <span className="text-xs font-medium text-subtext-light dark:text-subtext-dark">
            {getToolAlias(message.tool_name)}...
          </span>
        </div>
      </div>
    );
  }

  if (message.type === "tool_result") {
    // Don't render tool results - they're redundant with tool_call messages
    return null;
  }

  if (message.type === "error") {
    return (
      <div className="flex justify-center mb-4 animate-in shake">
        <div className="bg-red-50 dark:bg-red-950/30 border border-red-100 dark:border-red-900/50 text-red-900 dark:text-red-200 rounded-2xl px-5 py-3 max-w-md text-sm shadow-sm backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-4 h-4 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center text-red-600 dark:text-red-400 text-[10px] font-bold">!</div>
            <p className="font-semibold">Something went wrong</p>
          </div>
          <p className="text-xs text-red-700 dark:text-red-300 ml-6">
            Please check the dev logs for more details.
          </p>
        </div>
      </div>
    );
  }

  return null;
}
