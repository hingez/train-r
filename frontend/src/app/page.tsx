"use client";

import { useState, useEffect } from "react";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { DisplayPanel } from "@/components/display/DisplayPanel";
import { NotificationBubble } from "@/components/ui/NotificationBubble";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { DisplayType } from "@/types/messages";

// WebSocket URL - change this to match your backend
const WS_URL = "ws://localhost:3000/ws";

export default function Home() {
  const { messages, sendMessage, sendConfirmation, connectionStatus, error } = useWebSocket(WS_URL);
  const [displayType, setDisplayType] = useState<DisplayType>("welcome");
  const [displayData, setDisplayData] = useState<Record<string, any> | undefined>();
  const [cachedDashboardData, setCachedDashboardData] = useState<Record<string, any> | undefined>();

  // Track upload status from WebSocket messages
  const [uploadStatus, setUploadStatus] = useState<{
    status: 'uploading' | 'complete' | 'error' | 'idle';
    current?: number;
    total?: number;
    error?: string;
  }>({ status: 'idle' });

  // Update display based on messages
  useEffect(() => {
    // Find the most recent display_update message
    const displayUpdates = messages.filter((m) => m.type === "display_update");
    if (displayUpdates.length > 0) {
      const lastUpdate = displayUpdates[displayUpdates.length - 1];
      if (lastUpdate.type === "display_update") {
        setDisplayType(lastUpdate.display_type);
        setDisplayData(lastUpdate.data);

        // Cache dashboard data when received
        if (lastUpdate.display_type === "dashboard" && lastUpdate.data) {
          setCachedDashboardData(lastUpdate.data);
        }
      }
    }
  }, [messages]);

  // Listen for upload messages
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;

    if (lastMessage.type === 'upload_progress') {
      setUploadStatus({
        status: 'uploading',
        current: lastMessage.current,
        total: lastMessage.total
      });
    } else if (lastMessage.type === 'upload_complete') {
      setUploadStatus({ status: 'complete' });
      // Clear after 5 seconds
      setTimeout(() => setUploadStatus({ status: 'idle' }), 5000);
    } else if (lastMessage.type === 'upload_error') {
      setUploadStatus({
        status: 'error',
        error: lastMessage.error
      });
      // Clear after 10 seconds
      setTimeout(() => setUploadStatus({ status: 'idle' }), 10000);
    }
  }, [messages]);

  const handleGoHome = () => {
    // Navigate directly to cached dashboard data without sending a message
    if (cachedDashboardData) {
      setDisplayType("dashboard");
      setDisplayData(cachedDashboardData);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Display Panel - 75% */}
      <div className="flex-1 h-full overflow-hidden">
        <DisplayPanel displayType={displayType} displayData={displayData} onGoHome={handleGoHome} />
      </div>

      {/* Chat Panel - 25% */}
      <div className="w-1/4 min-w-[300px] h-full border-l bg-muted/10">
        <ChatPanel
          messages={messages}
          onSendMessage={sendMessage}
          onSendConfirmation={sendConfirmation}
          connectionStatus={connectionStatus}
        />
      </div>

      {/* Upload Notification Bubble */}
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
        <NotificationBubble
          status={uploadStatus.status}
          current={uploadStatus.current}
          total={uploadStatus.total}
          error={uploadStatus.error}
        />
      </div>

      {/* Error Toast (simple version) */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-destructive text-destructive-foreground px-4 py-2 rounded-md shadow-lg z-50">
          {error}
        </div>
      )}
    </div>
  );
}
