import { Card, CardContent } from "@/components/ui/card";
import { Calendar, TrendingUp, Zap, Target } from "lucide-react";
import type { PlanStats } from "@/lib/trainingPlanUtils";

interface SummaryStatsProps {
  stats: PlanStats;
}

export function SummaryStats({ stats }: SummaryStatsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card className="rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wide text-subtext-light dark:text-subtext-dark">Total Weeks</p>
              <p className="text-3xl font-bold tracking-tight text-text-light dark:text-text-dark">{stats.totalWeeks}</p>
              <p className="text-xs text-subtext-light dark:text-subtext-dark">{stats.totalWorkouts} workouts</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-purple-50 dark:bg-purple-900/20 text-primary flex items-center justify-center">
              <Calendar className="h-5 w-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wide text-subtext-light dark:text-subtext-dark">Peak Week</p>
              <p className="text-3xl font-bold tracking-tight text-text-light dark:text-text-dark">Week {stats.peakWeek.weekNumber}</p>
              <p className="text-xs text-subtext-light dark:text-subtext-dark">
                {stats.peakWeek.hours}h • {stats.peakWeek.tss} TSS
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-orange-50 dark:bg-orange-900/20 text-orange-500 flex items-center justify-center">
              <Zap className="h-5 w-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wide text-subtext-light dark:text-subtext-dark">Weekly Avg</p>
              <p className="text-3xl font-bold tracking-tight text-text-light dark:text-text-dark">{stats.avgWeeklyHours}h</p>
              <p className="text-xs text-subtext-light dark:text-subtext-dark">{stats.avgWeeklyTss} TSS/week</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-500 flex items-center justify-center">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wide text-subtext-light dark:text-subtext-dark">
                {stats.daysUntilRace !== null && stats.daysUntilRace > 0 ? "Race Countdown" : "Status"}
              </p>
              {stats.daysUntilRace !== null ? (
                stats.daysUntilRace > 0 ? (
                  <>
                    <p className="text-3xl font-bold tracking-tight text-text-light dark:text-text-dark">{stats.daysUntilRace}</p>
                    <p className="text-xs text-subtext-light dark:text-subtext-dark">days to go</p>
                  </>
                ) : (
                  <>
                    <p className="text-2xl font-semibold tracking-tight text-text-light dark:text-text-dark">Complete</p>
                    <p className="text-xs text-subtext-light dark:text-subtext-dark">Event finished</p>
                  </>
                )
              ) : (
                <>
                  <p className="text-3xl font-bold tracking-tight text-subtext-light/50">--</p>
                  <p className="text-xs text-subtext-light dark:text-subtext-dark">No date set</p>
                </>
              )}
            </div>
            <div className="w-10 h-10 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-500 flex items-center justify-center">
              <Target className="h-5 w-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
