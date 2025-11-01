"""Load tool definitions from JSON files and convert to OpenAI function format."""
import json
from pathlib import Path
from typing import Any


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
