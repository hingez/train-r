export interface AthleteProfile {
  ftp: number;
  weight_kg: number;
  goal_event: string;
  goal_date: string;
  training_philosophy: string;
  current_status: string;
}

export interface DayWorkout {
  type: string;
  duration_min: number;
  tss: number;
  desc: string;
}

export interface WeekSchedule {
  monday: DayWorkout;
  tuesday: DayWorkout;
  wednesday: DayWorkout;
  thursday: DayWorkout;
  friday: DayWorkout;
  saturday: DayWorkout;
  sunday: DayWorkout;
}

export interface Week {
  iso_week: string;
  start_date: string;
  target_hours: number;
  target_tss: number;
  schedule: WeekSchedule;
}

export interface TrainingPhase {
  phase_name: string;
  description: string;
  weeks: Week[];
}

export interface TrainingPlan {
  athlete_profile: AthleteProfile;
  training_plan: TrainingPhase[];
}

export interface DailySummary {
  date: string;
  day_name: string;
  iso_week: string;
  phase_name: string;
  type: string;
  duration_min: number;
  tss: number;
  description: string;
  week_target_hours: number;
  week_target_tss: number;
}
