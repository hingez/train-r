import { useState } from "react";
import { PlanHeader } from "./PlanHeader";
import { PlanOverview } from "./overview/PlanOverview";
import { WeeklyCalendar } from "./weekly/WeeklyCalendar";
import { DailyDetails } from "./daily/DailyDetails";
import type { TrainingPlan, DailySummary } from "@/types/trainingPlan";

type ViewMode = "overview" | "weekly" | "daily";

interface TrainingPlanDisplayProps {
  planData: TrainingPlan;
  summarizedData: DailySummary[];
}

export function TrainingPlanDisplay({ planData }: TrainingPlanDisplayProps) {
  const [currentView, setCurrentView] = useState<ViewMode>("overview");
  const [selectedWeekIndex, setSelectedWeekIndex] = useState<number>(0);
  const [selectedPhase, setSelectedPhase] = useState<string | null>(null);

  const handleViewSchedule = () => {
    setCurrentView("weekly");
  };

  const handleWeekClick = (weekIndex: number) => {
    setSelectedWeekIndex(weekIndex);
    setCurrentView("daily");
  };

  const handleBackToCalendar = () => {
    setCurrentView("weekly");
  };

  const handleBackToOverview = () => {
    setSelectedPhase(null);
    setCurrentView("overview");
  };

  const handlePhaseClick = (phaseName: string) => {
    setSelectedPhase(phaseName);
    setCurrentView("weekly");
  };

  const handlePrevWeek = () => {
    if (selectedWeekIndex > 0) {
      setSelectedWeekIndex(selectedWeekIndex - 1);
    }
  };

  const handleNextWeek = () => {
    const totalWeeks = planData.training_plan.reduce(
      (sum, phase) => sum + phase.weeks.length,
      0
    );
    if (selectedWeekIndex < totalWeeks - 1) {
      setSelectedWeekIndex(selectedWeekIndex + 1);
    }
  };

  return (
    <div className="p-8 overflow-y-auto h-full">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-2">Training Plan</h1>
          {currentView !== "overview" && (
            <button
              onClick={handleBackToOverview}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
            >
              <span>←</span> Back to Overview
            </button>
          )}
        </div>

        <PlanHeader profile={planData.athlete_profile} />

        {currentView === "overview" && (
          <PlanOverview
            plan={planData}
            onViewSchedule={handleViewSchedule}
            onPhaseClick={handlePhaseClick}
          />
        )}

        {currentView === "weekly" && (
          <WeeklyCalendar
            plan={planData}
            onWeekClick={handleWeekClick}
            selectedPhase={selectedPhase}
          />
        )}

        {currentView === "daily" && (
          <DailyDetails
            plan={planData}
            selectedWeekIndex={selectedWeekIndex}
            onBack={handleBackToCalendar}
            onPrevWeek={handlePrevWeek}
            onNextWeek={handleNextWeek}
          />
        )}
      </div>
    </div>
  );
}
