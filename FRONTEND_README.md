# Train-R Frontend

A modern, responsive frontend for the Train-R cycling coach application, built with Next.js and shadcn/ui.

## Architecture

### Stack
- **Framework**: Next.js 15+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: React hooks
- **Communication**: WebSocket for real-time chat
- **Backend**: FastAPI + WebSocket

### Layout
- **75% Display Panel** (left): Dynamic content area that shows different views based on conversation (Workouts, Charts, Welcome screen).
- **25% Chat Panel** (right): Real-time chat interface with the AI coach.

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+ with uv
- Environment variables set in `.env` (see root README)

### Installation

1. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Install Backend Dependencies** (from project root)
   ```bash
   uv sync
   ```

### Running the Application

The easiest way to run the full stack is using the unified startup command from the project root:

```bash
uv run train-r
```

This starts:
- **Backend API** at `http://localhost:3000`
- **Frontend** at `http://localhost:3001`

### Using the Application

1. Open http://localhost:3001 in your browser
2. You'll see the welcome screen in the display panel
3. Use the chat panel to interact with the AI coach
4. Try asking:
   - "Create a sweet spot workout for me"
   - "I want a 60-minute endurance ride"
   - "Generate a threshold workout"

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css      # Global styles & theme variables
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main application page
│   ├── components/
│   │   ├── ui/              # shadcn/ui components (Button, Input, Card, etc.)
│   │   ├── chat/            # Chat-specific components
│   │   ├── display/         # Display panel components
│   │   └── charts/          # Recharts visualizations
│   ├── hooks/
│   │   └── useWebSocket.ts  # WebSocket connection hook
│   ├── types/
│   │   └── messages.ts      # TypeScript type definitions
│   └── lib/
│       └── utils.ts         # Utility functions
├── package.json
├── tailwind.config.ts
└── tsconfig.json
```

## Display Types

The display panel can show different views based on the conversation:

1. **Welcome** - Initial greeting and capabilities overview
2. **Tool Execution** - Real-time status when executing tool calls
3. **Workout** - Shows created workout details, profile chart, and schedule
4. **Charts** - Training analytics

## Development Notes

### Styling
- Uses Tailwind CSS v4
- Theme colors are defined in `src/app/globals.css` using CSS variables
- Components are built with shadcn/ui patterns

### WebSocket
- Connects to `ws://localhost:3000/ws`
- Automatically attempts to reconnect if the connection drops

## Troubleshooting

### WebSocket won't connect
- Ensure backend is running on port 3000
- Check browser console for errors
- Verify `WS_URL` in `src/app/page.tsx` matches the backend port

### Styles missing
- Ensure `globals.css` is imported in `layout.tsx`
- Check `tailwind.config.ts` content paths

## License

Part of the Train-R project.
