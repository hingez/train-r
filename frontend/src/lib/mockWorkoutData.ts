import type { WorkoutData, WorkoutSegment } from "@/types/workout";
import { formatTime, calculateTrainingZone } from "@/types/workout";

/**
 * Generate mock sweet spot workout data
 * Sweet Spot = 88-94% FTP, typically 3x12-15min intervals
 */
export function generateSweetSpotWorkout(ftp: number = 300): WorkoutData {
  const segments: WorkoutSegment[] = [];
  let currentTime = 0;

  // Warmup: 10 minutes, ramping from 40% to 70% FTP
  const warmupSteps = 10;
  const warmupStartPower = Math.round(ftp * 0.4);
  const warmupEndPower = Math.round(ftp * 0.7);
  const warmupPowerStep = (warmupEndPower - warmupStartPower) / warmupSteps;

  for (let i = 0; i < warmupSteps; i++) {
    const power = Math.round(warmupStartPower + (warmupPowerStep * i));
    segments.push({
      time: formatTime(currentTime),
      duration: 60,
      power,
      zone: "warmup",
      trainingZone: calculateTrainingZone(power, ftp),
      label: i === 0 ? "Warmup" : undefined,
    });
    currentTime += 60;
  }

  // Interval 1: 12 minutes at 91% FTP (sweet spot)
  const intervalPower = Math.round(ftp * 0.91);

  // Break interval into 1-minute segments for better visualization
  for (let i = 0; i < 12; i++) {
    segments.push({
      time: formatTime(currentTime),
      duration: 60,
      power: intervalPower,
      zone: "sweetspot",
      trainingZone: calculateTrainingZone(intervalPower, ftp),
      label: i === 0 ? "Interval 1" : undefined,
    });
    currentTime += 60;
  }

  // Recovery 1: 3 minutes at 50% FTP
  const recoveryPower = Math.round(ftp * 0.5);
  for (let i = 0; i < 3; i++) {
    segments.push({
      time: formatTime(currentTime),
      duration: 60,
      power: recoveryPower,
      zone: "recovery",
      trainingZone: calculateTrainingZone(recoveryPower, ftp),
      label: i === 0 ? "Recovery" : undefined,
    });
    currentTime += 60;
  }

  // Interval 2: 12 minutes at 91% FTP
  for (let i = 0; i < 12; i++) {
    segments.push({
      time: formatTime(currentTime),
      duration: 60,
      power: intervalPower,
      zone: "sweetspot",
      trainingZone: calculateTrainingZone(intervalPower, ftp),
      label: i === 0 ? "Interval 2" : undefined,
    });
    currentTime += 60;
  }

  // Recovery 2: 3 minutes at 50% FTP
  for (let i = 0; i < 3; i++) {
    segments.push({
      time: formatTime(currentTime),
      duration: 60,
      power: recoveryPower,
      zone: "recovery",
      trainingZone: calculateTrainingZone(recoveryPower, ftp),
      label: i === 0 ? "Recovery" : undefined,
    });
    currentTime += 60;
  }

  // Interval 3: 12 minutes at 91% FTP
  for (let i = 0; i < 12; i++) {
    segments.push({
      time: formatTime(currentTime),
      duration: 60,
      power: intervalPower,
      zone: "sweetspot",
      trainingZone: calculateTrainingZone(intervalPower, ftp),
      label: i === 0 ? "Interval 3" : undefined,
    });
    currentTime += 60;
  }

  // Cooldown: 8 minutes, ramping from 70% to 40% FTP
  const cooldownSteps = 8;
  const cooldownStartPower = Math.round(ftp * 0.7);
  const cooldownEndPower = Math.round(ftp * 0.4);
  const cooldownPowerStep = (cooldownStartPower - cooldownEndPower) / cooldownSteps;

  for (let i = 0; i < cooldownSteps; i++) {
    const power = Math.round(cooldownStartPower - (cooldownPowerStep * i));
    segments.push({
      time: formatTime(currentTime),
      duration: 60,
      power,
      zone: "cooldown",
      trainingZone: calculateTrainingZone(power, ftp),
      label: i === 0 ? "Cooldown" : undefined,
    });
    currentTime += 60;
  }

  return {
    segments,
    ftp,
    totalDuration: currentTime,
    workoutName: "Sweet Spot 60min",
    description: "3x12min at 91% FTP with 3min recoveries",
  };
}

/**
 * Generate sample data for testing with different FTP values
 */
export function generateMockWorkout(ftp: number = 300): WorkoutData {
  return generateSweetSpotWorkout(ftp);
}
