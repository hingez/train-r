"use client";

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
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-purple-50 dark:bg-purple-900/20 text-primary flex items-center justify-center ring-1 ring-primary/10">
            <Target className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Goal Event</h3>
            <p className="font-bold text-foreground truncate max-w-[150px]">{profile.goal_event}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 flex items-center justify-center ring-1 ring-blue-500/10">
            <Calendar className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Race Date</h3>
            <p className="font-bold text-foreground">{goalDate}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="hover:shadow-md transition-shadow">
        <CardContent className="p-4 flex items-center gap-4">
          <div className="h-12 w-12 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 flex items-center justify-center ring-1 ring-green-500/10">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Stats</h3>
            <p className="font-bold text-foreground">{profile.ftp}W <span className="text-muted-foreground font-normal sm:text-xs">• {profile.weight_kg}kg</span></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
