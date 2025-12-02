import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DisplayType } from "@/types/messages";
import { Activity, Bike, TrendingUp } from "lucide-react";
import { WorkoutChart } from "@/components/charts/WorkoutChart";
import { generateMockWorkout } from "@/lib/mockWorkoutData";
import { TrainingPlanDisplay } from "@/components/training-plan/TrainingPlanDisplay";

interface DisplayPanelProps {
  displayType: DisplayType;
  displayData?: Record<string, any>;
}

export function DisplayPanel({ displayType, displayData }: DisplayPanelProps) {
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
      <div className="flex items-center justify-center h-full">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Executing: {displayData?.tool_name}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
            <p className="text-sm text-muted-foreground text-center">
              {displayData?.status === "executing" && "Processing your request..."}
            </p>
          </CardContent>
        </Card>
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
        {/* Workout Profile Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Workout Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <WorkoutChart workoutData={workoutData} showFTPLine={true} />
          </CardContent>
        </Card>

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
      />
    );
  }

  return null;
}
