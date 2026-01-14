import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DisplayType } from "@/types/messages";
import type { DashboardData } from "@/types/dashboard";
import { Activity, Bike, TrendingUp } from "lucide-react";
import { WorkoutChart } from "@/components/charts/WorkoutChart";
import { generateMockWorkout } from "@/lib/mockWorkoutData";
import { TrainingPlanDisplay } from "@/components/training-plan/TrainingPlanDisplay";
import { Dashboard } from "@/components/dashboard/Dashboard";
import { LoadingDisplay } from "@/components/dashboard/LoadingDisplay";
import { HomeButton } from "@/components/ui/HomeButton";
import { CyclistClimbingAnimation } from "@/components/ui/cyclist-climbing-animation";

interface DisplayPanelProps {
  displayType: DisplayType;
  displayData?: Record<string, any>;
  onGoHome?: () => void;
}

export function DisplayPanel({ displayType, displayData, onGoHome }: DisplayPanelProps) {
  if (displayType === "welcome") {
    return (
      <div className="flex items-center justify-center h-full bg-background p-8">
        <div className="max-w-3xl w-full space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-lg bg-primary-muted mb-4">
              <Bike className="h-10 w-10 text-primary" />
            </div>
            <h1 className="text-4xl font-bold tracking-tight">Train-R</h1>
            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
              AI-powered cycling coach ready to help you achieve your goals
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6 text-center space-y-3">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-muted">
                  <Activity className="h-6 w-6 text-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Analyze History</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Review training history and performance trends
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6 text-center space-y-3">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-muted">
                  <Bike className="h-6 w-6 text-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Create Workouts</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Generate custom workouts for your goals
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6 text-center space-y-3">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-muted">
                  <TrendingUp className="h-6 w-6 text-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Training Plans</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Build comprehensive training programs
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Call to Action */}
          <div className="text-center pt-4">
            <p className="text-sm text-muted-foreground">
              Start by asking me to create a workout or analyze your training history
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (displayType === "tool_execution") {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-b from-background-light to-gray-50 dark:from-background-dark dark:to-gray-900">
        <div className="flex flex-col items-center gap-4">
          <div className="scale-75">
            <CyclistClimbingAnimation />
          </div>
          <div className="text-center">
            <p className="text-lg font-semibold text-foreground mb-1">
              {displayData?.tool_name || "Working"}
            </p>
            <p className="text-sm text-muted-foreground">
              {displayData?.status === "executing" && "Processing your request..."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (displayType === "workout") {
    // Use real workout data if available, otherwise fall back to mock data
    const workoutData = displayData?.workout_data
      ? displayData.workout_data
      : generateMockWorkout(300);

    return (
      <div className="p-8 space-y-6 overflow-y-auto h-full">
        {onGoHome && (
          <div className="mb-4">
            <HomeButton onClick={onGoHome} />
          </div>
        )}
        {/* Workout Profile Chart */}
        <WorkoutChart workoutData={workoutData} showFTPLine={true} />

        {/* Workout Details */}
        <Card>
          <CardHeader>
            <CardTitle>Workout Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium">Workout Name:</p>
                <p className="text-sm text-muted-foreground">{workoutData.workoutName}</p>
              </div>
              <div>
                <p className="text-sm font-medium">Duration:</p>
                <p className="text-sm text-muted-foreground">
                  {Math.round(workoutData.totalDuration / 60)} minutes
                </p>
              </div>
              <div>
                <p className="text-sm font-medium">FTP:</p>
                <p className="text-sm text-muted-foreground">{workoutData.ftp}W</p>
              </div>
              <div>
                <p className="text-sm font-medium">Description:</p>
                <p className="text-sm text-muted-foreground">{workoutData.description}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium">Workout File:</p>
              <p className="text-sm text-muted-foreground">{displayData?.workout_file || "N/A"}</p>
            </div>
            <div>
              <p className="text-sm font-medium">Scheduled Time:</p>
              <p className="text-sm text-muted-foreground">{displayData?.scheduled_time || "N/A"}</p>
            </div>

            <div className="bg-muted p-4 rounded-md mt-4">
              <p className="text-xs text-muted-foreground">
                Your workout has been created and scheduled in intervals.icu.
                You can view it in your calendar and modify it if needed.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (displayType === "charts") {
    return (
      <div className="p-8">
        {onGoHome && (
          <div className="mb-4">
            <HomeButton onClick={onGoHome} />
          </div>
        )}
        <Card>
          <CardHeader>
            <CardTitle>Training Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Charts and analytics will be displayed here. (POC - To be implemented)
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (displayType === "training_plan") {
    return (
      <TrainingPlanDisplay
        planData={displayData?.plan}
        summarizedData={displayData?.summarized}
        onGoHome={onGoHome}
      />
    );
  }

  if (displayType === "dashboard") {
    return (
      <div className="h-full overflow-y-auto">
        <Dashboard dashboardData={displayData as DashboardData} />
      </div>
    );
  }

  if (displayType === "loading") {
    return <LoadingDisplay message={displayData?.message} />;
  }

  return null;
}
