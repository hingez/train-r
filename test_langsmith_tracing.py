"""Test script to verify LangSmith tracing with thread linking."""
import asyncio
import logging
import uuid
from src.config import AppConfig
from src.integrations.llm_client import LLMClient
from src.services.coach_service import CoachService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('train-r')


async def test_tracing():
    """Test that traces are linked together via thread_id (session_id)."""

    print("=" * 60)
    print("LangSmith Thread Linking Test")
    print("=" * 60)

    # Load config
    config = AppConfig.from_env()
    config.create_directories()

    # Initialize wrapped LLM client
    llm_client = LLMClient(
        api_key=config.llm_api_key,
        base_url=config.llm_base_url,
        langsmith_tracing_enabled=config.langsmith_tracing_enabled,
        langsmith_api_key=config.langsmith_api_key,
        langsmith_project=config.langsmith_project
    )

    print(f"\n✓ LLM Client initialized")
    print(f"  - LangSmith enabled: {llm_client.langsmith_enabled}")
    print(f"  - Project: {config.langsmith_project}")

    # Initialize CoachService
    coach_service = CoachService(llm_client, config)

    print(f"\n✓ CoachService initialized")
    print(f"  - LangSmith tracing: {llm_client.langsmith_enabled}")

    # Generate a session ID to group all traces together (simulates a user session)
    session_id = str(uuid.uuid4())
    print(f"\n✓ Session ID: {session_id}")
    print("  All traces in this session will be grouped under this thread_id")

    print("\n" + "=" * 60)
    print("Test 1: Simple Question (CoachAgent trace)")
    print("=" * 60)

    response1 = await coach_service.process_message(
        "What's a good warm-up duration?",
        request_id="test-msg-1",
        session_id=session_id
    )

    print(f"\nResponse: {response1[:100]}...")
    print("✓ Traced as 'CoachAgent' with thread_id")

    print("\n" + "=" * 60)
    print("Test 2: Follow-up Question (Same Thread)")
    print("=" * 60)

    response2 = await coach_service.process_message(
        "What about cool-down?",
        request_id="test-msg-2",
        session_id=session_id
    )

    print(f"\nResponse: {response2[:100]}...")
    print("✓ Traced as 'CoachAgent' with same thread_id")

    print("\n" + "=" * 60)
    print("Test 3: Tool Call (CoachAgent + WorkoutGenerator traces)")
    print("=" * 60)

    response3 = await coach_service.process_message(
        "Create a 60 minute sweet spot workout at 250W FTP with 4x10min intervals at 88-92% FTP",
        request_id="test-msg-3",
        session_id=session_id
    )

    print(f"\nResponse: {response3[:150]}...")
    print("✓ Traced as 'CoachAgent' + nested 'WorkoutGenerator' with same thread_id")

    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)
    print(f"\nAll traces should appear grouped in LangSmith UI:")
    print(f"  Project: {config.langsmith_project}")
    print(f"  Thread ID: {session_id}")
    print("\nIn LangSmith, navigate to:")
    print("  1. Go to your project")
    print("  2. Look for 'Threads' view or filter by thread_id")
    print("  3. All 3 messages should be grouped under the same thread")
    print("\nTrace names you should see:")
    print("  - 'CoachAgent' (3 traces - one per message)")
    print("  - 'WorkoutGenerator' (1 trace - nested under 3rd message)")
    print("\nCheck: https://smith.langchain.com")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tracing())
