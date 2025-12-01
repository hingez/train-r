/**
 * UI-friendly aliases for tool names
 * Maps internal tool names to user-facing display names
 */
export const TOOL_ALIASES: Record<string, string> = {
  create_one_off_workout: "Creating workout",
  get_user_workout_history: "Fetching workout history",
};

/**
 * Get the user-friendly name for a tool
 * Falls back to the original tool name if no alias is defined
 */
export function getToolAlias(toolName: string): string {
  return TOOL_ALIASES[toolName] || toolName;
}
