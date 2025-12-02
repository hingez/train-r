import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Calendar, TrendingUp, Zap, Target } from "lucide-react";
import type { PlanStats } from "@/lib/trainingPlanUtils";

interface SummaryStatsProps {
  stats: PlanStats;
}

export function SummaryStats({ stats }: SummaryStatsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="metric-label">Total Weeks</p>
              <p className="text-3xl font-bold tracking-tight">{stats.totalWeeks}</p>
              <p className="text-xs text-muted-foreground">{stats.totalWorkouts} workouts</p>
            </div>
            <Calendar className="h-5 w-5 text-muted-foreground/50" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="metric-label">Peak Week</p>
              <p className="text-3xl font-bold tracking-tight">Week {stats.peakWeek.weekNumber}</p>
              <p className="text-xs text-muted-foreground">
                {stats.peakWeek.hours}h • {stats.peakWeek.tss} TSS
              </p>
            </div>
            <Zap className="h-5 w-5 text-muted-foreground/50" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="metric-label">Weekly Average</p>
              <p className="text-3xl font-bold tracking-tight">{stats.avgWeeklyHours}h</p>
              <p className="text-xs text-muted-foreground">{stats.avgWeeklyTss} TSS/week</p>
            </div>
            <TrendingUp className="h-5 w-5 text-muted-foreground/50" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="metric-label">
                {stats.daysUntilRace !== null && stats.daysUntilRace > 0 ? "Days to Race" : "Race Status"}
              </p>
              {stats.daysUntilRace !== null ? (
                stats.daysUntilRace > 0 ? (
                  <>
                    <p className="text-3xl font-bold tracking-tight">{stats.daysUntilRace}</p>
                    <p className="text-xs text-muted-foreground">days remaining</p>
                  </>
                ) : (
                  <>
                    <p className="text-2xl font-semibold tracking-tight">Complete</p>
                    <p className="text-xs text-muted-foreground">Race day passed</p>
                  </>
                )
              ) : (
                <>
                  <p className="text-3xl font-bold tracking-tight text-muted-foreground/50">--</p>
                  <p className="text-xs text-muted-foreground">No date set</p>
                </>
              )}
            </div>
            <Target className="h-5 w-5 text-muted-foreground/50" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
