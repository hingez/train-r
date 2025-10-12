"""Load tool definitions from JSON files and convert to Gemini Tool format."""
import json
from pathlib import Path
from google.genai.types import Tool, FunctionDeclaration


def load_tools(tools_dir: str = "tools") -> list[Tool]:
    """Load all tool definitions from JSON files in the tools directory.

    Args:
        tools_dir: Directory containing tool JSON definition files

    Returns:
        List of Gemini Tool objects
    """
    tools_path = Path(tools_dir)

    if not tools_path.exists():
        return []

    # Load all JSON files
    tool_files = sorted(tools_path.glob("*.json"))

    if not tool_files:
        return []

    # Convert each JSON file to FunctionDeclaration
    function_declarations = []

    for tool_file in tool_files:
        with open(tool_file, 'r') as f:
            tool_def = json.load(f)

        # Create FunctionDeclaration
        func_declaration = FunctionDeclaration(
            name=tool_def["name"],
            description=tool_def.get("description", ""),
            parameters=tool_def.get("parameters", {})
        )

        function_declarations.append(func_declaration)

    # Return single Tool with all function declarations
    return [Tool(function_declarations=function_declarations)]


def get_tool_names(tools: list[Tool]) -> list[str]:
    """Extract tool names from Tool objects for reference.

    Args:
        tools: List of Tool objects

    Returns:
        List of tool names
    """
    names = []
    for tool in tools:
        for func in tool.function_declarations:
            names.append(func.name)
    return names
