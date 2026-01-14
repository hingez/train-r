## Project Summary
Train-R is an LLM-powered cycling coach that helps users with training plans, providing individual workouts and overall plans to reach specific goals. The system uses Gemini for conversational AI with tool-calling capabilities and integrates with intervals.icu for workout scheduling. You can view the API spec for intervals in the intervals_icu_api_spec.json file.

INITALLY THIS WILL BE USED ONLY BY ME IN A DEVELOPMENT CAPACITY AND I WILL ALWAYS JUST RUN LOCALLY SO JUST BEAR THAT IN MIND

## Git Practices
- Write clear, descriptive commit messages. Start with a short summary (50 characters or less), then add details if needed.
- Make small, focused commits that do one thing. This makes code easier to review and revert if needed.
Commit often—it's better to have many small commits than one giant one. Don't write a huge message and write is as a human would.

## Project Setup
- This is a Python project and `uv` is used for project and package management.
- Use `uv run ...`, `uv add ...` and `uv sync` to run Python and manage packages while keeping pyproject files up to date.
- Ensure you create sufficient logging with logs/.log files; only use print statements where required for functionality.

## Developement Practices
- Utilize .env for sensitive information.
- Use the config file to hold necessary constants and variables.
- Only write additional .md files when you are asked to.
- Use a single LLM client (client address) when calling Gemini. If you need to add functionality, do it there so it can be shared across the project.
- NO FEATURE CREEP JUST ADD THE FEATURES YOU ARE ASKED TO ADD, ALWAYS ASK IF YOU ARE UNSURE
- Ensure to leave succinct, clear comments where required to understand the function of code.
- Write straightforward, readable code. Avoid unnecessary complexity, clever tricks, or overengineering. Choose the simplest solution that solves the problem.
- Only implement features and functions that are currently required. Don't add code for hypothetical use cases or future needs or "just in case" scenarios.
- Eliminate code duplication. Extract related logic into reusable functions, classes, or modules. Each piece of knowledge should have a single authoritative representation.
- Only use generally accepted best practices from large technology companies like Google.
