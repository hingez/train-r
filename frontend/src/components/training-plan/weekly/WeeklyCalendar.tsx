import { WeekCard } from "./WeekCard";
import { getAllWeeks } from "@/lib/trainingPlanUtils";
import type { TrainingPlan } from "@/types/trainingPlan";

interface WeeklyCalendarProps {
  plan: TrainingPlan;
  onWeekClick: (weekIndex: number) => void;
  selectedPhase?: string | null;
}

export function WeeklyCalendar({ plan, onWeekClick, selectedPhase }: WeeklyCalendarProps) {
  const allWeeks = getAllWeeks(plan);

  // Find max TSS for bar scaling
  const maxTss = Math.max(...allWeeks.map(w => w.target_tss));

  // Group weeks by phase for section headers
  const weeksByPhase: { phaseName: string; description: string; weeks: { week: typeof allWeeks[0]; weekIndex: number }[] }[] = [];

  let weekIndex = 0;
  plan.training_plan.forEach((phase) => {
    const phaseWeeks = phase.weeks.map((week) => {
      const result = { week, weekIndex };
      weekIndex++;
      return result;
    });

    weeksByPhase.push({
      phaseName: phase.phase_name,
      description: phase.description,
      weeks: phaseWeeks
    });
  });

  return (
    <div>
      {weeksByPhase.map((phase, phaseIdx) => {
        // Skip phases if filtering by selected phase
        if (selectedPhase && phase.phaseName !== selectedPhase) {
          return null;
        }

        return (
          <div key={phaseIdx} className="mb-8">
            {/* Phase Header */}
            <div className="mb-4">
              <h2 className="text-2xl font-bold">{phase.phaseName}</h2>
              <p className="text-sm text-muted-foreground mt-1">{phase.description}</p>
            </div>

            {/* Week Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {phase.weeks.map(({ week, weekIndex: idx }) => (
                <WeekCard
                  key={week.iso_week}
                  week={week}
                  weekNumber={idx + 1}
                  maxTss={maxTss}
                  onClick={() => onWeekClick(idx)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
