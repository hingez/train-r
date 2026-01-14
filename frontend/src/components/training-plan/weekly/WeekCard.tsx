import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { MiniWorkoutGrid } from "./MiniWorkoutGrid";
import { getWeekDateRange } from "@/lib/trainingPlanUtils";
import type { Week } from "@/types/trainingPlan";

interface WeekCardProps {
  week: Week;
  weekNumber: number;
  maxTss: number;
  onClick: () => void;
}

export function WeekCard({ week, weekNumber, maxTss, onClick }: WeekCardProps) {
  const dateRange = getWeekDateRange(week.start_date);
  const tssPercentage = (week.target_tss / maxTss) * 100;

  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Week {weekNumber}</h3>
          <div className="text-xs text-muted-foreground">
            {week.target_hours}h | {week.target_tss} TSS
          </div>
        </div>
        <p className="text-xs text-muted-foreground">{dateRange}</p>
      </CardHeader>
      <CardContent>
        <MiniWorkoutGrid schedule={week.schedule} />

        {/* TSS Bar Indicator */}
        <div className="mt-3">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${tssPercentage}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
