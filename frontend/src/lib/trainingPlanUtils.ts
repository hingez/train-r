import type { TrainingPlan, Week, TrainingPhase } from "@/types/trainingPlan";

export interface PlanStats {
  totalWeeks: number;
  totalWorkouts: number;
  peakWeek: {
    weekNumber: number;
    hours: number;
    tss: number;
  };
  avgWeeklyTss: number;
  avgWeeklyHours: number;
  daysUntilRace: number | null;
}

export function calculatePlanStats(plan: TrainingPlan): PlanStats {
  let totalWeeks = 0;
  let totalWorkouts = 0;
  let totalTss = 0;
  let totalHours = 0;
  let peakWeek = { weekNumber: 0, hours: 0, tss: 0 };
  let weekCounter = 0;

  plan.training_plan.forEach((phase) => {
    phase.weeks.forEach((week) => {
      weekCounter++;
      totalWeeks++;
      totalTss += week.target_tss;
      totalHours += week.target_hours;

      // Count workouts (non-rest days)
      Object.values(week.schedule).forEach((day) => {
        if (day.duration_min > 0) {
          totalWorkouts++;
        }
      });

      // Track peak week
      if (week.target_tss > peakWeek.tss) {
        peakWeek = {
          weekNumber: weekCounter,
          hours: week.target_hours,
          tss: week.target_tss
        };
      }
    });
  });

  // Calculate days until race
  let daysUntilRace: number | null = null;
  if (plan.athlete_profile.goal_date) {
    const raceDate = new Date(plan.athlete_profile.goal_date);
    const today = new Date();
    const diffTime = raceDate.getTime() - today.getTime();
    daysUntilRace = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  return {
    totalWeeks,
    totalWorkouts,
    peakWeek,
    avgWeeklyTss: Math.round(totalTss / totalWeeks),
    avgWeeklyHours: Math.round((totalHours / totalWeeks) * 10) / 10,
    daysUntilRace
  };
}

export function getWeekDateRange(startDate: string): string {
  const start = new Date(startDate);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);

  const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  const startMonth = monthNames[start.getMonth()];
  const startDay = start.getDate();
  const endMonth = monthNames[end.getMonth()];
  const endDay = end.getDate();
  const year = end.getFullYear();

  if (startMonth === endMonth) {
    return `${startMonth} ${startDay}-${endDay}, ${year}`;
  } else {
    return `${startMonth} ${startDay} - ${endMonth} ${endDay}, ${year}`;
  }
}

export function groupWeeksByPhase(plan: TrainingPlan): Record<string, Week[]> {
  const grouped: Record<string, Week[]> = {};

  plan.training_plan.forEach((phase) => {
    grouped[phase.phase_name] = phase.weeks;
  });

  return grouped;
}

export function isRecoveryWeek(targetHours: number, phaseWeeks: Week[]): boolean {
  if (phaseWeeks.length === 0) return false;

  const phaseAvg = phaseWeeks.reduce((sum, week) => sum + week.target_hours, 0) / phaseWeeks.length;
  return targetHours < phaseAvg * 0.7;
}

export function getAllWeeks(plan: TrainingPlan): Week[] {
  const allWeeks: Week[] = [];

  plan.training_plan.forEach((phase) => {
    allWeeks.push(...phase.weeks);
  });

  return allWeeks;
}

export function getWeekNumber(plan: TrainingPlan, week: Week): number {
  const allWeeks = getAllWeeks(plan);
  return allWeeks.findIndex(w => w.iso_week === week.iso_week) + 1;
}

export function formatDuration(minutes: number): string {
  if (minutes === 0) return "Rest";

  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (hours > 0 && mins > 0) {
    return `${hours}h ${mins}m`;
  } else if (hours > 0) {
    return `${hours}h`;
  } else {
    return `${mins}m`;
  }
}

export function getPhaseColor(phaseName: string): string {
  if (phaseName.includes("Base 1")) return "bg-blue-500";
  if (phaseName.includes("Base 2")) return "bg-blue-600";
  if (phaseName.includes("Base 3")) return "bg-blue-700";
  if (phaseName.includes("Build 1")) return "bg-orange-500";
  if (phaseName.includes("Build 2")) return "bg-orange-600";
  if (phaseName.includes("Peak")) return "bg-red-500";
  if (phaseName.includes("Taper")) return "bg-green-500";
  if (phaseName.includes("Race")) return "bg-purple-500";
  return "bg-gray-500";
}
