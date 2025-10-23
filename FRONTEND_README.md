# Train-R Frontend POC

A lightweight proof-of-concept frontend for the Train-R cycling coach application.

## Architecture

### Stack
- **Frontend**: React + TypeScript + Vite
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React hooks
- **Communication**: WebSocket for real-time chat
- **Backend**: FastAPI + WebSocket

### Layout
- **75% Display Panel** (left): Dynamic content area that shows different views based on conversation
- **25% Chat Panel** (right): Real-time chat interface with the AI coach

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+ with uv
- Environment variables set in `.env`:
  ```
  GEMINI_API_KEY=your_key_here
  INTERVALS_API_KEY=your_key_here
  ```

### Installation

1. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Install Backend Dependencies** (from project root)
   ```bash
   uv add fastapi uvicorn websockets
   ```

### Running the Application

You need **two terminal windows**:

#### Terminal 1: Backend Server
```bash
# From project root
uv run scripts/dev_server.py
```

This starts the FastAPI server at `http://localhost:8000` with:
- WebSocket endpoint: `ws://localhost:8000/ws`
- Health check: `http://localhost:8000/api/health`

#### Terminal 2: Frontend Dev Server
```bash
# From project root
cd frontend
npm run dev
```

This starts the Vite dev server at `http://localhost:5173`

### Using the Application

1. Open http://localhost:5173 in your browser
2. You'll see the welcome screen in the display panel (75% left side)
3. Use the chat panel (25% right side) to interact with the AI coach
4. Try asking:
   - "Create a sweet spot workout for me"
   - "I want a 60-minute endurance ride"
   - "Generate a threshold workout"

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Basic UI components (Button, Input, Card)
│   │   ├── chat/            # Chat-specific components
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ChatPanel.tsx
│   │   └── display/         # Display panel components
│   │       └── DisplayPanel.tsx
│   ├── hooks/
│   │   └── useWebSocket.ts  # WebSocket connection hook
│   ├── types/
│   │   └── messages.ts      # TypeScript type definitions
│   ├── lib/
│   │   └── utils.ts         # Utility functions (cn)
│   ├── App.tsx              # Main application component
│   ├── index.css            # Tailwind + theme configuration
│   └── main.tsx             # Entry point
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Display Types

The display panel can show different views based on the conversation:

1. **Welcome** - Initial greeting and capabilities overview
2. **Tool Execution** - Real-time status when executing tool calls
3. **Workout** - Shows created workout details and schedule
4. **Charts** - Training analytics (placeholder for future implementation)

## Message Flow

1. User types message in chat input → sends via WebSocket
2. Backend processes with Gemini API
3. If tool call needed:
   - Backend executes tool (e.g., create workout)
   - Sends `tool_call` message
   - Sends `tool_result` message
   - Sends `display_update` to change display panel
4. Backend sends final `assistant_message` with text response
5. Frontend updates both chat and display panel

## Development Notes

### Hot Module Replacement (HMR)
Vite provides instant updates when you edit files - just save and see changes immediately.

### WebSocket Reconnection
The frontend automatically attempts to reconnect if the WebSocket connection drops.

### Styling
- Uses Tailwind CSS utility classes
- Custom theme colors defined in `index.css`
- shadcn/ui-inspired component patterns

## Future Enhancements

This is a POC. Potential improvements:

- [ ] Parse ZWO files and visualize workout power profile
- [ ] Add real training charts with Recharts
- [ ] Implement dark mode toggle
- [ ] Add user authentication
- [ ] Persist conversation history
- [ ] Mobile responsive design
- [ ] Streaming LLM responses with typing indicators
- [ ] Upload and analyze workout files
- [ ] Integration with real intervals.icu data

## Troubleshooting

### WebSocket won't connect
- Ensure backend is running on port 8000
- Check CORS_ORIGINS in `.env` includes `http://localhost:5173`
- Verify no firewall blocking local connections

### Tailwind styles not working
- Make sure `npm run dev` is running (Vite processes Tailwind)
- Check `tailwind.config.js` content paths include your files

### Import errors
- Verify path aliases in `tsconfig.app.json` and `vite.config.ts`
- Ensure all dependencies are installed with `npm install`

## API Documentation

### WebSocket Message Types

**From Client:**
```typescript
{
  type: "user_message",
  content: string
}
```

**From Server:**
```typescript
// Assistant response
{
  type: "assistant_message",
  content: string,
  timestamp: string
}

// Tool execution started
{
  type: "tool_call",
  tool_name: string,
  tool_args: object,
  timestamp: string
}

// Tool execution completed
{
  type: "tool_result",
  tool_name: string,
  result: object,
  success: boolean,
  timestamp: string
}

// Update display panel
{
  type: "display_update",
  display_type: "welcome" | "workout" | "charts" | "tool_execution",
  data?: object,
  timestamp: string
}

// Error occurred
{
  type: "error",
  message: string,
  timestamp: string
}
```

## License

Part of the Train-R project.
