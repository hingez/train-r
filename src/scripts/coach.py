"""Train-R: LLM-powered cycling coach CLI.

This is a command-line interface for the Train-R cycling coach.
It uses the refactored CoachService with LLM client abstraction.
"""
import asyncio

from src.config import AppConfig
from src.utils.logger import setup_logger
from src.models.gemini_client import GeminiClient
from src.services.coach_service import CoachService
from src.services.workout_service import WorkoutService


async def main():
    """Main application loop."""
    # Initialize logging (clears log file)
    logger = setup_logger()

    print("=" * 60)
    print("Train-R Cycling Coach (Refactored Architecture)")
    print("=" * 60)

    try:
        # Load configuration from environment
        config = AppConfig.from_env()
        logger.info("Configuration loaded successfully")

        # Create required directories
        config.create_directories()

        # Initialize LLM client
        llm_client = GeminiClient(api_key=config.gemini_api_key)
        logger.info(f"LLM client initialized: {config.model_name}")

        # Initialize workout service first (needed by coach service)
        workout_service = WorkoutService(llm_client, config)

        # Initialize coach service with workout service
        coach_service = CoachService(llm_client, config, workout_service)

        print(f"Coach initialized with {len(coach_service.tool_names)} tools")
        print(f"Available tools: {', '.join(coach_service.tool_names)}")
        print("\nType 'quit' to exit, 'reset' to clear conversation history\n")

    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        return
    except Exception as e:
        logger.error(f"Failed to initialize: {e}", exc_info=True)
        print(f"\nInitialization Error: {e}")
        return

    # Conversation loop
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if user_input.lower() == 'reset':
            coach_service.reset_conversation()
            print("Conversation history cleared.")
            continue

        if not user_input:
            continue

        try:
            # Process message through coach service
            # The service now handles all the complexity of tool calling
            response = await coach_service.process_message(user_input)

            # Display response
            if response:
                print(f"\nTrain-R: {response}")
            else:
                print("\nTrain-R: (No response)")

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            print(f"\nTrain-R: Sorry, an error occurred: {str(e)}")
            print("Please try again or type 'reset' to clear the conversation.")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
