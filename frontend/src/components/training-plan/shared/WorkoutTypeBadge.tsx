import { cn } from "@/lib/utils";
import { getWorkoutTypeConfig } from "./workoutTypeConfig";

interface WorkoutTypeBadgeProps {
  type: string;
  size?: "sm" | "md" | "lg";
}

export function WorkoutTypeBadge({ type, size = "md" }: WorkoutTypeBadgeProps) {
  const config = getWorkoutTypeConfig(type);

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
    lg: "text-sm px-3 py-1.5"
  };

  return (
    <div
      className={cn(
        "rounded-md font-medium inline-flex items-center border border-transparent",
        config.color,
        config.darkColor,
        config.textColor,
        config.darkTextColor,
        sizeClasses[size]
      )}
    >
      <span>{config.label}</span>
    </div>
  );
}
