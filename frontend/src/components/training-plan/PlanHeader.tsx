import { Card, CardContent } from "@/components/ui/card";
import { Calendar, Target, TrendingUp } from "lucide-react";
import type { AthleteProfile } from "@/types/trainingPlan";

interface PlanHeaderProps {
  profile: AthleteProfile;
}

export function PlanHeader({ profile }: PlanHeaderProps) {
  const goalDate = new Date(profile.goal_date).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric"
  });

  return (
    <Card className="mb-6">
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="flex items-start gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-muted shrink-0">
              <Target className="h-5 w-5 text-primary" />
            </div>
            <div className="min-w-0">
              <h4 className="metric-label mb-1">Goal Event</h4>
              <p className="text-sm font-medium truncate">{profile.goal_event}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-muted shrink-0">
              <Calendar className="h-5 w-5 text-primary" />
            </div>
            <div className="min-w-0">
              <h4 className="metric-label mb-1">Race Date</h4>
              <p className="text-sm font-medium">{goalDate}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-muted shrink-0">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            <div className="min-w-0">
              <h4 className="metric-label mb-1">Philosophy</h4>
              <p className="text-sm font-medium truncate">{profile.training_philosophy}</p>
            </div>
          </div>
        </div>

        <div className="pt-4 border-t space-y-3">
          <h4 className="metric-label">Current Status</h4>
          <p className="text-sm text-foreground/80 leading-relaxed">{profile.current_status}</p>
        </div>

        <div className="mt-4 pt-4 border-t flex gap-6 text-sm">
          <div className="flex items-baseline gap-2">
            <span className="metric-label">FTP:</span>
            <span className="text-lg font-semibold">{profile.ftp}W</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="metric-label">Weight:</span>
            <span className="text-lg font-semibold">{profile.weight_kg}kg</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
