/**
 * Type definitions for athlete dashboard data.
 *
 * These types define the structure of data received from the backend
 * for displaying performance charts and analytics.
 */

/**
 * Weekly training load data point.
 */
export interface WeeklyLoad {
  week_start: string;
  total_tss: number;
  total_time_hours: number;
  total_distance_km: number;
  workout_count: number;
}

/**
 * Power curve data point for a specific duration.
 */
export interface PowerCurvePoint {
  duration: string; // "5s", "1min", "5min", "20min", etc.
  duration_seconds: number;
  watts: number;
}

/**
 * Power curve data containing both 30-day and all-time curves.
 */
export interface PowerCurveData {
  thirty_day: PowerCurvePoint[];
  all_time: PowerCurvePoint[];
}

/**
 * Weekly zone distribution data point.
 */
export interface ZoneDistribution {
  week_start: string;
  zone_1_hours: number;
  zone_2_hours: number;
  zone_3_hours: number;
  zone_4_hours: number;
  zone_5_hours: number;
}

/**
 * Recent activity summary.
 */
export interface RecentActivity {
  date: string;
  name: string | null;
  duration: number; // seconds
  tss: number;
  np: number;
  avg_power: number;
  if: number;
  distance_km: number | null;
}

/**
 * Complete dashboard data structure.
 * This is the top-level data sent from backend to frontend.
 */
export interface DashboardData {
  weekly_load: WeeklyLoad[];
  power_curve: PowerCurveData;
  zone_distribution: ZoneDistribution[];
  recent_activities: RecentActivity[];
}
