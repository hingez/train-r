import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { WorkoutTypeBadge } from "../shared/WorkoutTypeBadge";
import { formatDuration } from "@/lib/trainingPlanUtils";

interface DayCardProps {
  dayName: string;
  date: string;
  type: string;
  durationMin: number;
  tss: number;
  description: string;
}

export function DayCard({ dayName, date, type, durationMin, tss, description }: DayCardProps) {
  const formattedDate = new Date(date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric"
  });

  return (
    <Card className="mb-3">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-lg">{dayName}</h3>
            <p className="text-sm text-muted-foreground">{formattedDate}</p>
          </div>
          <WorkoutTypeBadge type={type} size="lg" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-6 mb-3">
          <div>
            <p className="text-xs text-muted-foreground">Duration</p>
            <p className="font-semibold">{formatDuration(durationMin)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">TSS</p>
            <p className="font-semibold">{tss}</p>
          </div>
        </div>
        <div>
          <p className="text-sm leading-relaxed">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}
