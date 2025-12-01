# Train-R

An AI cycling coach that creates personalized workouts and uploads them to intervals.icu.

## How it Works

Train-R uses an LLM (Gemini 2.5 Flash) with function calling to provide conversational coaching. When you request a workout:

1. The LLM understands your request (workout type, duration, intensity)
2. Calls the `create_one_off_workout` tool with your FTP and parameters
3. Generates a structured ZWO workout file (Zwift format)
4. Uploads it to your intervals.icu calendar (scheduled 1 hour ahead)
5. Responds with confirmation and workout details

The conversation maintains context, so you can refine workouts or ask follow-up questions. Built with FastAPI backend and React frontend.

## Setup

1. **Install dependencies**
   ```bash
   git clone https://github.com/hingez/train-r.git
   cd train-r
   uv sync
   ```

2. **Create `.env` file**
   ```bash
   cp .env.example .env
   ```

3. **Add your API keys to `.env`**
   ```env
   LLM_API_KEY=your_key_here           # Get at: https://aistudio.google.com/apikey
   INTERVALS_API_KEY=your_key_here     # Get at: https://intervals.icu/settings#developer
   ```

## Usage

```bash
uv run train-r
```

Opens at http://localhost:3001 (backend at http://localhost:3000)

### Example

```
You: I need a 90 minute sweet spot workout, my FTP is 340 watts
Train-R: [Creates and uploads workout to intervals.icu]
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ (for frontend)
