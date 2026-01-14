import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { DayCard } from "./DayCard";
import type { Week, TrainingPlan } from "@/types/trainingPlan";
import { getAllWeeks, getWeekDateRange } from "@/lib/trainingPlanUtils";

interface DailyDetailsProps {
  plan: TrainingPlan;
  selectedWeekIndex: number;
  onBack: () => void;
  onPrevWeek: () => void;
  onNextWeek: () => void;
}

const dayOrder = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const;

export function DailyDetails({
  plan,
  selectedWeekIndex,
  onBack,
  onPrevWeek,
  onNextWeek
}: DailyDetailsProps) {
  const allWeeks = getAllWeeks(plan);
  const week = allWeeks[selectedWeekIndex];
  const weekNumber = selectedWeekIndex + 1;

  if (!week) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">Week not found</p>
        <Button onClick={onBack} className="mt-4">
          Back to Calendar
        </Button>
      </div>
    );
  }

  const dateRange = getWeekDateRange(week.start_date);

  // Find phase for breadcrumb
  const phase = plan.training_plan.find(p => p.weeks.some(w => w.iso_week === week.iso_week));

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-4 text-sm text-muted-foreground">
        <button onClick={onBack} className="hover:text-foreground">
          Plan Overview
        </button>
        {phase && (
          <>
            {" > "}
            <span>{phase.phase_name}</span>
          </>
        )}
        {" > "}
        <span className="text-foreground font-medium">Week {weekNumber}</span>
      </div>

      {/* Week Navigation */}
      <div className="flex items-center justify-between mb-6">
        <Button
          variant="outline"
          onClick={onPrevWeek}
          disabled={selectedWeekIndex === 0}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Previous Week
        </Button>

        <div className="text-center">
          <h2 className="text-2xl font-bold">Week {weekNumber}</h2>
          <p className="text-sm text-muted-foreground">{dateRange}</p>
          <p className="text-sm text-muted-foreground mt-1">
            {week.target_hours}h | {week.target_tss} TSS
          </p>
        </div>

        <Button
          variant="outline"
          onClick={onNextWeek}
          disabled={selectedWeekIndex === allWeeks.length - 1}
        >
          Next Week
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </div>

      {/* Daily Cards */}
      <div className="space-y-3">
        {dayOrder.map((day) => {
          const workout = week.schedule[day];
          // Calculate date for this day
          const weekStart = new Date(week.start_date);
          const dayIndex = dayOrder.indexOf(day);
          const dayDate = new Date(weekStart);
          dayDate.setDate(weekStart.getDate() + dayIndex);

          return (
            <DayCard
              key={day}
              dayName={day.charAt(0).toUpperCase() + day.slice(1)}
              date={dayDate.toISOString().split("T")[0]}
              type={workout.type}
              durationMin={workout.duration_min}
              tss={workout.tss}
              description={workout.desc}
            />
          );
        })}
      </div>

      {/* Bottom Navigation */}
      <div className="flex justify-center mt-6">
        <Button variant="outline" onClick={onBack}>
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back to Calendar
        </Button>
      </div>
    </div>
  );
}
