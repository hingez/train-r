import { useState, useEffect } from "react";
import { ChatPanel } from "./components/chat/ChatPanel";
import { DisplayPanel } from "./components/display/DisplayPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import type { DisplayType } from "./types/messages";

// WebSocket URL - change this to match your backend
const WS_URL = "ws://localhost:3000/ws";

function App() {
  const { messages, sendMessage, sendConfirmation, connectionStatus, error } = useWebSocket(WS_URL);
  const [displayType, setDisplayType] = useState<DisplayType>("welcome");
  const [displayData, setDisplayData] = useState<Record<string, any> | undefined>();

  // Update display based on messages
  useEffect(() => {
    // Find the most recent display_update message
    const displayUpdates = messages.filter((m) => m.type === "display_update");
    if (displayUpdates.length > 0) {
      const lastUpdate = displayUpdates[displayUpdates.length - 1];
      if (lastUpdate.type === "display_update") {
        setDisplayType(lastUpdate.display_type);
        setDisplayData(lastUpdate.data);
      }
    }
  }, [messages]);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Display Panel - 75% */}
      <div className="flex-1">
        <DisplayPanel displayType={displayType} displayData={displayData} />
      </div>

      {/* Chat Panel - 25% */}
      <div className="w-1/4 min-w-[300px]">
        <ChatPanel
          messages={messages}
          onSendMessage={sendMessage}
          onSendConfirmation={sendConfirmation}
          connectionStatus={connectionStatus}
        />
      </div>

      {/* Error Toast (simple version) */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-destructive text-destructive-foreground px-4 py-2 rounded-md shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}

export default App;
