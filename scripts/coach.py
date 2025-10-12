"""Train-R: LLM-powered cycling coach with tool support."""
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Import our custom modules
from train_r.core.config import get_model_name, get_model_config
from train_r.tools.loader import load_tools, get_tool_names
from train_r.tools.handler import handle_tool_call
from train_r.core.conversation import ConversationManager
from train_r.core.logger import setup_logger, get_logger

# Get project root (parent of scripts directory)
PROJECT_ROOT = Path(__file__).parent.parent


def load_prompt(prompt_path: str) -> str:
    """Load the system prompt from file."""
    full_path = PROJECT_ROOT / prompt_path
    with open(full_path, 'r') as f:
        return f.read()


def has_tool_calls(response) -> bool:
    """Check if response contains tool calls.

    Args:
        response: Model response object

    Returns:
        True if response has tool calls, False otherwise
    """
    if not hasattr(response, 'candidates') or not response.candidates:
        return False

    candidate = response.candidates[0]
    if not hasattr(candidate, 'content') or not candidate.content:
        return False

    # Check if any parts are function calls
    for part in candidate.content.parts:
        if hasattr(part, 'function_call') and part.function_call:
            return True

    return False


def get_tool_calls(response) -> list:
    """Extract tool calls from response.

    Args:
        response: Model response object

    Returns:
        List of tool call objects
    """
    tool_calls = []

    if not hasattr(response, 'candidates') or not response.candidates:
        return tool_calls

    candidate = response.candidates[0]
    if not hasattr(candidate, 'content') or not candidate.content:
        return tool_calls

    # Extract function calls
    for part in candidate.content.parts:
        if hasattr(part, 'function_call') and part.function_call:
            tool_calls.append(part.function_call)

    return tool_calls


def get_text_response(response) -> str:
    """Extract text from response.

    Args:
        response: Model response object

    Returns:
        Text content or empty string
    """
    if not hasattr(response, 'candidates') or not response.candidates:
        return ""

    candidate = response.candidates[0]
    if not hasattr(candidate, 'content') or not candidate.content:
        return ""

    # Extract text parts
    text_parts = []
    for part in candidate.content.parts:
        if hasattr(part, 'text'):
            text_parts.append(part.text)

    return "\n".join(text_parts)


def main():
    """Main application loop."""
    # Initialize logging (clears log file)
    logger = setup_logger()

    # Load environment variables
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    intervals_api_key = os.getenv("INTERVALS_API_KEY")

    if not gemini_api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        return

    if not intervals_api_key:
        print("Error: INTERVALS_API_KEY not found in .env file")
        return

    # Load system prompt
    system_prompt = load_prompt("prompts/system_prompt.txt")

    # Load tools
    tools = load_tools(str(PROJECT_ROOT / "train_r/tools/definitions"))
    tool_names = get_tool_names(tools)

    logger.info(f"Loaded {len(tool_names)} tools: {', '.join(tool_names)}")

    print("=== Train-R Cycling Coach ===")
    print(f"Loaded {len(tool_names)} tools: {', '.join(tool_names)}")
    print("Type 'quit' to exit\n")

    # Initialize Gemini client
    client = genai.Client(api_key=gemini_api_key)

    # Initialize conversation manager
    conversation = ConversationManager()

    # Model configuration with tools
    model_name = get_model_name()
    config = get_model_config(system_prompt, tools=tools)

    # Conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        # Add user message to conversation
        conversation.add_user_message(user_input)
        logger.info(f"USER: {user_input}")

        # Generate response with tools
        response = client.models.generate_content(
            model=model_name,
            contents=conversation.get_history(),
            config=config
        )

        # Check for tool calls
        while has_tool_calls(response):
            # Add model response with tool calls to history
            conversation.add_model_response(response)

            # Get tool calls
            tool_calls = get_tool_calls(response)

            # Execute each tool call
            for tool_call in tool_calls:
                # Handle tool call with both API keys
                result = handle_tool_call(tool_call, gemini_api_key, intervals_api_key)

                # Add tool response to conversation
                conversation.add_tool_response(tool_call, result)

            # Call model again with tool results
            response = client.models.generate_content(
                model=model_name,
                contents=conversation.get_history(),
                config=config
            )

        # Add final model response to history
        conversation.add_model_response(response)

        # Extract and display text response
        text_response = get_text_response(response)

        if text_response:
            logger.info(f"ASSISTANT: {text_response}")
            print(f"\nTrain-R: {text_response}")
        else:
            logger.warning("ASSISTANT: No response generated")
            print("\nTrain-R: (No response)")


if __name__ == "__main__":
    main()
