export interface WorkoutTypeConfig {
  color: string;
  darkColor: string;
  textColor: string;
  darkTextColor: string;
  label: string;
}

export const WORKOUT_TYPE_CONFIG: Record<string, WorkoutTypeConfig> = {
  Rest: {
    color: "bg-muted",
    darkColor: "dark:bg-muted",
    textColor: "text-muted-foreground",
    darkTextColor: "dark:text-muted-foreground",
    label: "Rest"
  },
  Intervals: {
    color: "bg-red-50",
    darkColor: "dark:bg-red-950/30",
    textColor: "text-red-700",
    darkTextColor: "dark:text-red-400",
    label: "Intervals"
  },
  Endurance: {
    color: "bg-blue-50",
    darkColor: "dark:bg-blue-950/30",
    textColor: "text-blue-700",
    darkTextColor: "dark:text-blue-400",
    label: "Endurance"
  },
  "Long Ride": {
    color: "bg-purple-50",
    darkColor: "dark:bg-purple-950/30",
    textColor: "text-purple-700",
    darkTextColor: "dark:text-purple-400",
    label: "Long Ride"
  },
  Tempo: {
    color: "bg-orange-50",
    darkColor: "dark:bg-orange-950/30",
    textColor: "text-orange-700",
    darkTextColor: "dark:text-orange-400",
    label: "Tempo"
  },
  Threshold: {
    color: "bg-amber-50",
    darkColor: "dark:bg-amber-950/30",
    textColor: "text-amber-700",
    darkTextColor: "dark:text-amber-400",
    label: "Threshold"
  },
  "VO2max": {
    color: "bg-red-50",
    darkColor: "dark:bg-red-950/30",
    textColor: "text-red-800",
    darkTextColor: "dark:text-red-300",
    label: "VO2max"
  },
  "Race Sim": {
    color: "bg-yellow-50",
    darkColor: "dark:bg-yellow-950/30",
    textColor: "text-yellow-800",
    darkTextColor: "dark:text-yellow-400",
    label: "Race Sim"
  },
  Opener: {
    color: "bg-yellow-50",
    darkColor: "dark:bg-yellow-950/30",
    textColor: "text-yellow-700",
    darkTextColor: "dark:text-yellow-400",
    label: "Opener"
  },
  "Cadence/Skills": {
    color: "bg-teal-50",
    darkColor: "dark:bg-teal-950/30",
    textColor: "text-teal-700",
    darkTextColor: "dark:text-teal-400",
    label: "Skills"
  },
  "RACE DAY": {
    color: "bg-amber-100",
    darkColor: "dark:bg-amber-900/40",
    textColor: "text-amber-900",
    darkTextColor: "dark:text-amber-300",
    label: "RACE DAY"
  },
  Recovery: {
    color: "bg-green-50",
    darkColor: "dark:bg-green-950/30",
    textColor: "text-green-700",
    darkTextColor: "dark:text-green-400",
    label: "Recovery"
  },
  Activation: {
    color: "bg-cyan-50",
    darkColor: "dark:bg-cyan-950/30",
    textColor: "text-cyan-700",
    darkTextColor: "dark:text-cyan-400",
    label: "Activation"
  }
};

export function getWorkoutTypeConfig(type: string): WorkoutTypeConfig {
  return WORKOUT_TYPE_CONFIG[type] || {
    color: "bg-muted",
    darkColor: "dark:bg-muted",
    textColor: "text-muted-foreground",
    darkTextColor: "dark:text-muted-foreground",
    label: type
  };
}
