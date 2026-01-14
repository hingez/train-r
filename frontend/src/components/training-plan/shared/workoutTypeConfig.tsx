import React from "react";
import {
  Zap,
  Activity,
  Coffee,
  Timer,
  Trophy,
  TrendingUp,
  Flame,
  Bike,
  Dumbbell
} from "lucide-react";

export interface WorkoutTypeConfig {
  color: string;
  darkColor: string;
  textColor: string;
  darkTextColor: string;
  label: string;
  icon: React.ReactNode;
}

export const WORKOUT_TYPE_CONFIG: Record<string, WorkoutTypeConfig> = {
  Rest: {
    color: "bg-muted",
    darkColor: "dark:bg-muted",
    textColor: "text-muted-foreground",
    darkTextColor: "dark:text-muted-foreground",
    label: "Rest",
    icon: <Coffee className="w-4 h-4" />
  },
  Intervals: {
    color: "bg-red-50",
    darkColor: "dark:bg-red-950/30",
    textColor: "text-red-700",
    darkTextColor: "dark:text-red-400",
    label: "Intervals",
    icon: <Zap className="w-4 h-4" />
  },
  Endurance: {
    color: "bg-blue-50",
    darkColor: "dark:bg-blue-950/30",
    textColor: "text-blue-700",
    darkTextColor: "dark:text-blue-400",
    label: "Endurance",
    icon: <Activity className="w-4 h-4" />
  },
  "Long Ride": {
    color: "bg-purple-50",
    darkColor: "dark:bg-purple-950/30",
    textColor: "text-purple-700",
    darkTextColor: "dark:text-purple-400",
    label: "Long Ride",
    icon: <Bike className="w-4 h-4" />
  },
  Tempo: {
    color: "bg-orange-50",
    darkColor: "dark:bg-orange-950/30",
    textColor: "text-orange-700",
    darkTextColor: "dark:text-orange-400",
    label: "Tempo",
    icon: <Timer className="w-4 h-4" />
  },
  Threshold: {
    color: "bg-amber-50",
    darkColor: "dark:bg-amber-950/30",
    textColor: "text-amber-700",
    darkTextColor: "dark:text-amber-400",
    label: "Threshold",
    icon: <Flame className="w-4 h-4" />
  },
  "VO2max": {
    color: "bg-red-50",
    darkColor: "dark:bg-red-950/30",
    textColor: "text-red-800",
    darkTextColor: "dark:text-red-300",
    label: "VO2max",
    icon: <Zap className="w-4 h-4" />
  },
  "Race Sim": {
    color: "bg-yellow-50",
    darkColor: "dark:bg-yellow-950/30",
    textColor: "text-yellow-800",
    darkTextColor: "dark:text-yellow-400",
    label: "Race Sim",
    icon: <Trophy className="w-4 h-4" />
  },
  Opener: {
    color: "bg-yellow-50",
    darkColor: "dark:bg-yellow-950/30",
    textColor: "text-yellow-700",
    darkTextColor: "dark:text-yellow-400",
    label: "Opener",
    icon: <Zap className="w-4 h-4" />
  },
  "Cadence/Skills": {
    color: "bg-teal-50",
    darkColor: "dark:bg-teal-950/30",
    textColor: "text-teal-700",
    darkTextColor: "dark:text-teal-400",
    label: "Skills",
    icon: <Dumbbell className="w-4 h-4" />
  },
  "RACE DAY": {
    color: "bg-amber-100",
    darkColor: "dark:bg-amber-900/40",
    textColor: "text-amber-900",
    darkTextColor: "dark:text-amber-300",
    label: "RACE DAY",
    icon: <Trophy className="w-4 h-4" />
  },
  Recovery: {
    color: "bg-green-50",
    darkColor: "dark:bg-green-950/30",
    textColor: "text-green-700",
    darkTextColor: "dark:text-green-400",
    label: "Recovery",
    icon: <Coffee className="w-4 h-4" />
  },
  Activation: {
    color: "bg-cyan-50",
    darkColor: "dark:bg-cyan-950/30",
    textColor: "text-cyan-700",
    darkTextColor: "dark:text-cyan-400",
    label: "Activation",
    icon: <TrendingUp className="w-4 h-4" />
  }
};

export function getWorkoutTypeConfig(type: string): WorkoutTypeConfig {
  return WORKOUT_TYPE_CONFIG[type] || {
    color: "bg-muted",
    darkColor: "dark:bg-muted",
    textColor: "text-muted-foreground",
    darkTextColor: "dark:text-muted-foreground",
    label: type,
    icon: <Activity className="w-4 h-4" />
  };
}
