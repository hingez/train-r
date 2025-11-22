"""Tests for tool loader functionality."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.tools.loader import load_tools, get_tool_names, load_tool_executors


class TestLoadTools:
    """Test load_tools function."""

    def test_loads_tools_from_json_files(self, tmp_path):
        """Should load and convert tool definitions from JSON files."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        # Create a tool definition file
        tool_def = {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        }
        (tools_dir / "test_tool.json").write_text(json.dumps(tool_def))

        tools = load_tools(str(tools_dir))

        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "test_tool"
        assert tools[0]["function"]["description"] == "A test tool"

    def test_loads_multiple_tools(self, tmp_path):
        """Should load all JSON files from directory."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        for i in range(3):
            tool_def = {"name": f"tool_{i}", "description": f"Tool {i}"}
            (tools_dir / f"tool_{i}.json").write_text(json.dumps(tool_def))

        tools = load_tools(str(tools_dir))

        assert len(tools) == 3
        names = {t["function"]["name"] for t in tools}
        assert names == {"tool_0", "tool_1", "tool_2"}

    def test_returns_empty_list_for_nonexistent_directory(self, tmp_path):
        """Should return empty list when directory doesn't exist."""
        tools = load_tools(str(tmp_path / "nonexistent"))

        assert tools == []

    def test_returns_empty_list_for_empty_directory(self, tmp_path):
        """Should return empty list when no JSON files exist."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        tools = load_tools(str(tools_dir))

        assert tools == []

    def test_converts_to_openai_format(self, tmp_path):
        """Should convert to OpenAI-compatible tool format."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        tool_def = {
            "name": "create_workout",
            "description": "Creates a workout",
            "parameters": {
                "type": "object",
                "properties": {
                    "ftp": {"type": "integer"},
                    "duration": {"type": "integer"}
                },
                "required": ["ftp", "duration"]
            }
        }
        (tools_dir / "create_workout.json").write_text(json.dumps(tool_def))

        tools = load_tools(str(tools_dir))

        assert tools[0] == {
            "type": "function",
            "function": {
                "name": "create_workout",
                "description": "Creates a workout",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ftp": {"type": "integer"},
                        "duration": {"type": "integer"}
                    },
                    "required": ["ftp", "duration"]
                }
            }
        }

    def test_handles_missing_optional_fields(self, tmp_path):
        """Should handle tools with missing optional fields."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        # Minimal tool definition
        tool_def = {"name": "minimal_tool"}
        (tools_dir / "minimal.json").write_text(json.dumps(tool_def))

        tools = load_tools(str(tools_dir))

        assert tools[0]["function"]["name"] == "minimal_tool"
        assert tools[0]["function"]["description"] == ""
        assert tools[0]["function"]["parameters"] == {}

    def test_sorts_tools_alphabetically(self, tmp_path):
        """Should return tools sorted by filename."""
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()

        # Create files in non-alphabetical order
        (tools_dir / "z_tool.json").write_text(json.dumps({"name": "z"}))
        (tools_dir / "a_tool.json").write_text(json.dumps({"name": "a"}))
        (tools_dir / "m_tool.json").write_text(json.dumps({"name": "m"}))

        tools = load_tools(str(tools_dir))

        # Should be sorted alphabetically
        names = [t["function"]["name"] for t in tools]
        assert names == ["a", "m", "z"]


class TestGetToolNames:
    """Test get_tool_names function."""

    def test_extracts_tool_names(self):
        """Should extract names from tool definitions."""
        tools = [
            {"type": "function", "function": {"name": "tool_a"}},
            {"type": "function", "function": {"name": "tool_b"}},
            {"type": "function", "function": {"name": "tool_c"}},
        ]

        names = get_tool_names(tools)

        assert names == ["tool_a", "tool_b", "tool_c"]

    def test_returns_empty_list_for_empty_tools(self):
        """Should return empty list for no tools."""
        names = get_tool_names([])

        assert names == []

    def test_preserves_order(self):
        """Should preserve the order of tools."""
        tools = [
            {"type": "function", "function": {"name": "third"}},
            {"type": "function", "function": {"name": "first"}},
            {"type": "function", "function": {"name": "second"}},
        ]

        names = get_tool_names(tools)

        assert names == ["third", "first", "second"]


class TestLoadToolExecutors:
    """Test load_tool_executors function."""

    def test_returns_empty_dict_for_nonexistent_directory(self, tmp_path):
        """Should return empty dict when definitions directory doesn't exist."""
        executors = load_tool_executors(str(tmp_path / "nonexistent"))

        assert executors == {}

    def test_returns_empty_dict_for_empty_directory(self, tmp_path):
        """Should return empty dict when no JSON files exist."""
        tools_dir = tmp_path / "tools"
        definitions_dir = tools_dir / "definitions"
        definitions_dir.mkdir(parents=True)

        executors = load_tool_executors(str(tools_dir))

        assert executors == {}

    def test_maps_tool_name_to_executor(self, tmp_path):
        """Should map tool names to their execute functions."""
        tools_dir = tmp_path / "tools"
        definitions_dir = tools_dir / "definitions"
        definitions_dir.mkdir(parents=True)

        # Create tool definition
        tool_def = {"name": "test_tool"}
        (definitions_dir / "test_tool.json").write_text(json.dumps(tool_def))

        # Mock the module import
        mock_module = Mock()
        mock_module.execute = Mock()

        with patch("src.tools.loader.importlib.import_module", return_value=mock_module):
            executors = load_tool_executors(str(tools_dir))

        assert "test_tool" in executors
        assert executors["test_tool"] is mock_module.execute

    def test_raises_on_missing_execute_function(self, tmp_path):
        """Should raise error when module has no execute function."""
        tools_dir = tmp_path / "tools"
        definitions_dir = tools_dir / "definitions"
        definitions_dir.mkdir(parents=True)

        tool_def = {"name": "broken_tool"}
        (definitions_dir / "broken_tool.json").write_text(json.dumps(tool_def))

        mock_module = Mock(spec=[])  # No execute attribute

        with patch("src.tools.loader.importlib.import_module", return_value=mock_module):
            with pytest.raises(ImportError, match="Failed to load executor"):
                load_tool_executors(str(tools_dir))

    def test_maps_create_one_off_workout_to_create_workout_tool(self, tmp_path):
        """Should map create_one_off_workout to create_workout_tool module."""
        tools_dir = tmp_path / "tools"
        definitions_dir = tools_dir / "definitions"
        definitions_dir.mkdir(parents=True)

        tool_def = {"name": "create_one_off_workout"}
        (definitions_dir / "create_one_off_workout.json").write_text(json.dumps(tool_def))

        mock_module = Mock()
        mock_module.execute = Mock()

        with patch("src.tools.loader.importlib.import_module", return_value=mock_module) as mock_import:
            load_tool_executors(str(tools_dir))

        # Should import from create_workout_tool module
        mock_import.assert_called_with("src.tools.create_workout_tool")

    def test_maps_get_user_workout_history_to_get_history_tool(self, tmp_path):
        """Should map get_user_workout_history to correct module."""
        tools_dir = tmp_path / "tools"
        definitions_dir = tools_dir / "definitions"
        definitions_dir.mkdir(parents=True)

        tool_def = {"name": "get_user_workout_history"}
        (definitions_dir / "get_user_workout_history.json").write_text(json.dumps(tool_def))

        mock_module = Mock()
        mock_module.execute = Mock()

        with patch("src.tools.loader.importlib.import_module", return_value=mock_module) as mock_import:
            load_tool_executors(str(tools_dir))

        # Should import from get_user_workout_history_tool module
        mock_import.assert_called_with("src.tools.get_user_workout_history_tool")

    def test_loads_multiple_executors(self, tmp_path):
        """Should load executors for all tool definitions."""
        tools_dir = tmp_path / "tools"
        definitions_dir = tools_dir / "definitions"
        definitions_dir.mkdir(parents=True)

        # Create multiple tool definitions
        for name in ["tool_a", "tool_b", "tool_c"]:
            tool_def = {"name": name}
            (definitions_dir / f"{name}.json").write_text(json.dumps(tool_def))

        mock_module = Mock()
        mock_module.execute = Mock()

        with patch("src.tools.loader.importlib.import_module", return_value=mock_module):
            executors = load_tool_executors(str(tools_dir))

        assert len(executors) == 3
        assert all(name in executors for name in ["tool_a", "tool_b", "tool_c"])

    def test_raises_on_import_error(self, tmp_path):
        """Should raise ImportError when module cannot be imported."""
        tools_dir = tmp_path / "tools"
        definitions_dir = tools_dir / "definitions"
        definitions_dir.mkdir(parents=True)

        tool_def = {"name": "missing_module"}
        (definitions_dir / "missing_module.json").write_text(json.dumps(tool_def))

        with patch("src.tools.loader.importlib.import_module", side_effect=ModuleNotFoundError("No module")):
            with pytest.raises(ImportError, match="Failed to load executor.*missing_module"):
                load_tool_executors(str(tools_dir))
