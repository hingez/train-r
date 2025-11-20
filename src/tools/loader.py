"""Load tool definitions from JSON files and convert to OpenAI function format."""
import json
import importlib
from pathlib import Path
from typing import Any, Callable, Dict


def load_tools(tools_dir: str = "tools") -> list[dict[str, Any]]:
    """Load all tool definitions from JSON files in the tools directory.

    Args:
        tools_dir: Directory containing tool JSON definition files

    Returns:
        List of OpenAI-compatible tool definitions
    """
    tools_path = Path(tools_dir)

    if not tools_path.exists():
        return []

    # Load all JSON files
    tool_files = sorted(tools_path.glob("*.json"))

    if not tool_files:
        return []

    # Convert each JSON file to OpenAI tool format
    tools = []

    for tool_file in tool_files:
        with open(tool_file, 'r') as f:
            tool_def = json.load(f)

        # Create OpenAI-compatible tool definition
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool_def["name"],
                "description": tool_def.get("description", ""),
                "parameters": tool_def.get("parameters", {})
            }
        }

        tools.append(openai_tool)

    return tools


def get_tool_names(tools: list[dict[str, Any]]) -> list[str]:
    """Extract tool names from tool definitions for reference.

    Args:
        tools: List of OpenAI-compatible tool definitions

    Returns:
        List of tool names
    """
    return [tool["function"]["name"] for tool in tools]


def load_tool_executors(tools_dir: str = "tools") -> Dict[str, Callable]:
    """Load all tool executor functions from Python modules.

    For each .json file in the definitions directory, loads the corresponding
    .py file and extracts its execute() function.

    Args:
        tools_dir: Directory containing tool definition files

    Returns:
        Dict mapping tool names to their execute functions
    """
    tools_path = Path(tools_dir)
    definitions_path = tools_path / "definitions"

    if not definitions_path.exists():
        return {}

    executors = {}

    # Find all JSON tool definitions
    tool_files = sorted(definitions_path.glob("*.json"))

    for tool_file in tool_files:
        # Read the tool definition to get the tool name
        with open(tool_file, 'r') as f:
            tool_def = json.load(f)

        tool_name = tool_def["name"]

        # Construct the module name (e.g., "create_one_off_workout" -> "create_workout_tool")
        # Tool names follow pattern: action_descriptor
        # Module names follow pattern: action_tool
        module_name = tool_file.stem  # e.g., "create_one_off_workout"

        # Map tool definition name to module name
        # create_one_off_workout -> create_workout_tool
        # get_user_workout_history -> get_user_workout_history_tool
        if module_name == "create_one_off_workout":
            module_name = "create_workout_tool"
        elif module_name == "get_user_workout_history":
            module_name = "get_user_workout_history_tool"
        else:
            # For future tools, assume they follow the pattern
            module_name = f"{module_name}_tool"

        try:
            # Import the tool module
            module = importlib.import_module(f"src.tools.{module_name}")

            # Get the execute function
            if hasattr(module, "execute"):
                executors[tool_name] = module.execute
            else:
                raise AttributeError(f"Module {module_name} has no execute() function")

        except Exception as e:
            raise ImportError(f"Failed to load executor for tool '{tool_name}': {e}")

    return executors
