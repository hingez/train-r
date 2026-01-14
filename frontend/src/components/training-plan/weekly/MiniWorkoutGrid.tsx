import { getWorkoutTypeConfig } from "../shared/workoutTypeConfig";
import type { WeekSchedule } from "@/types/trainingPlan";

interface MiniWorkoutGridProps {
  schedule: WeekSchedule;
}

const dayOrder = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const;

export function MiniWorkoutGrid({ schedule }: MiniWorkoutGridProps) {
  return (
    <div className="grid grid-cols-7 gap-1">
      {dayOrder.map((day) => {
        const workout = schedule[day];
        const config = getWorkoutTypeConfig(workout.type);

        return (
          <div
            key={day}
            className="aspect-square flex items-center justify-center text-lg"
            title={`${day.charAt(0).toUpperCase() + day.slice(1)}: ${workout.type}`}
          >
            {config.icon}
          </div>
        );
      })}
    </div>
  );
}
