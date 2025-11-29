import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DisplayType } from "@/types/messages";
import { Activity, Bike, TrendingUp } from "lucide-react";
import { WorkoutChart } from "@/components/charts/WorkoutChart";
import { generateMockWorkout } from "@/lib/mockWorkoutData";

interface DisplayPanelProps {
  displayType: DisplayType;
  displayData?: Record<string, any>;
}

export function DisplayPanel({ displayType, displayData }: DisplayPanelProps) {
  if (displayType === "welcome") {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
        <div className="max-w-2xl text-center space-y-6">
          <div className="flex justify-center">
            <Bike className="h-16 w-16 text-primary" />
          </div>
          <h1 className="text-4xl font-bold">Welcome to Train-R</h1>
          <p className="text-lg text-muted-foreground">
            Your AI-powered cycling coach is ready to help you achieve your goals.
          </p>
          <div className="grid grid-cols-3 gap-4 mt-8">
            <Card>
              <CardHeader>
                <Activity className="h-6 w-6 mb-2 text-primary" />
                <CardTitle className="text-sm">Analyze History</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  Review your training history and performance
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Bike className="h-6 w-6 mb-2 text-primary" />
                <CardTitle className="text-sm">Create Workouts</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  Generate custom workouts for your goals
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <TrendingUp className="h-6 w-6 mb-2 text-primary" />
                <CardTitle className="text-sm">Training Plans</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  Build comprehensive training programs
                </p>
              </CardContent>
            </Card>
          </div>
          <p className="text-sm text-muted-foreground mt-8">
            Start by asking me to create a workout or analyze your training history.
          </p>
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

  return null;
}
