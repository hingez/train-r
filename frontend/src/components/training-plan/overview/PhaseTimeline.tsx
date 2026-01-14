import { getPhaseColor } from "@/lib/trainingPlanUtils";
import type { TrainingPhase } from "@/types/trainingPlan";

interface PhaseTimelineProps {
  phases: TrainingPhase[];
  onPhaseClick?: (phaseName: string) => void;
}

export function PhaseTimeline({ phases, onPhaseClick }: PhaseTimelineProps) {
  const totalWeeks = phases.reduce((sum, phase) => sum + phase.weeks.length, 0);

  return (
    <section className="bg-card-light dark:bg-card-dark rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
      <div className="p-5 border-b border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-lg">Training Phases</h3>
      </div>
      <div className="p-5">
        <div className="flex gap-1 h-12 rounded-lg overflow-hidden shadow-inner">
          {phases.map((phase, index) => {
            const weekCount = phase.weeks.length;
            const widthPercentage = (weekCount / totalWeeks) * 100;
            const color = getPhaseColor(phase.phase_name);

            return (
              <div
                key={index}
                className={`${color} flex items-center justify-center text-white text-xs font-medium px-2 cursor-pointer hover:brightness-110 transition-all`}
                style={{ width: `${widthPercentage}%` }}
                onClick={() => onPhaseClick?.(phase.phase_name)}
                title={`${phase.phase_name}\n${weekCount} weeks\n\n${phase.description}`}
              >
                <span className="truncate">{phase.phase_name}</span>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-subtext-light dark:text-subtext-dark mt-2 font-medium">
          <span>Week 1</span>
          <span>Week {totalWeeks}</span>
        </div>
      </div>
    </section>
  );
}
