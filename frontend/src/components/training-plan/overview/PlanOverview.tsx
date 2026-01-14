import { Button } from "@/components/ui/button";
import { ChevronRight } from "lucide-react";
import { PhaseTimeline } from "./PhaseTimeline";
import { ProgressionChart } from "./ProgressionChart";
import { SummaryStats } from "./SummaryStats";
import { calculatePlanStats } from "@/lib/trainingPlanUtils";
import type { TrainingPlan } from "@/types/trainingPlan";

interface PlanOverviewProps {
  plan: TrainingPlan;
  onViewSchedule: () => void;
  onPhaseClick?: (phaseName: string) => void;
}

export function PlanOverview({ plan, onViewSchedule, onPhaseClick }: PlanOverviewProps) {
  const stats = calculatePlanStats(plan);

  return (
    <div>
      <SummaryStats stats={stats} />
      <PhaseTimeline phases={plan.training_plan} onPhaseClick={onPhaseClick} />
      <ProgressionChart plan={plan} />

      <div className="flex justify-center mt-6">
        <Button onClick={onViewSchedule} size="lg">
          View Detailed Schedule
          <ChevronRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
