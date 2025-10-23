export type WorkoutZone = "warmup" | "recovery" | "endurance" | "tempo" | "sweetspot" | "threshold" | "vo2max" | "cooldown";

// Standard 7-zone training system
export type TrainingZone = "Z1" | "Z2" | "Z3" | "Z4" | "Z5" | "Z6" | "Z7";

export interface ZoneDefinition {
  zone: TrainingZone;
  name: string;
  minPercent: number;  // % of FTP
  maxPercent: number;  // % of FTP
  color: string;
  description: string;
}

export interface WorkoutSegment {
  time: string;          // Format: "MM:SS" or "HH:MM:SS"
  duration: number;      // Duration in seconds
  power: number;         // Power in watts
  zone: WorkoutZone;     // Training zone
  trainingZone?: TrainingZone; // Calculated Z1-Z7
  label?: string;        // Optional label (e.g., "Interval 1")
}

export interface WorkoutData {
  segments: WorkoutSegment[];
  ftp: number;           // Functional Threshold Power
  totalDuration: number; // Total workout duration in seconds
  workoutName?: string;
  description?: string;
}

// Helper to format seconds to MM:SS or HH:MM:SS
export function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// Helper to get zone color
export function getZoneColor(zone: WorkoutZone): string {
  const zoneColors: Record<WorkoutZone, string> = {
    warmup: "hsl(var(--secondary))",
    recovery: "hsl(var(--muted))",
    endurance: "hsl(142, 76%, 56%)",    // Green
    tempo: "hsl(48, 96%, 53%)",          // Yellow
    sweetspot: "hsl(var(--primary))",   // Purple (primary)
    threshold: "hsl(25, 95%, 53%)",      // Orange
    vo2max: "hsl(0, 84%, 60%)",          // Red
    cooldown: "hsl(var(--secondary))",
  };
  return zoneColors[zone];
}

// Helper to calculate % of FTP
export function getPowerPercent(power: number, ftp: number): number {
  return Math.round((power / ftp) * 100);
}

// Training zones based on % of FTP (standard 7-zone model)
export const TRAINING_ZONES: ZoneDefinition[] = [
  {
    zone: "Z1",
    name: "Active Recovery",
    minPercent: 0,
    maxPercent: 55,
    color: "hsl(200, 70%, 85%)",  // Light blue
    description: "Very easy, recovery pace"
  },
  {
    zone: "Z2",
    name: "Endurance",
    minPercent: 56,
    maxPercent: 75,
    color: "hsl(142, 76%, 56%)",  // Green
    description: "Aerobic endurance"
  },
  {
    zone: "Z3",
    name: "Tempo",
    minPercent: 76,
    maxPercent: 87,
    color: "hsl(48, 96%, 53%)",   // Yellow
    description: "Tempo, muscular endurance"
  },
  {
    zone: "Z4",
    name: "Sweet Spot",
    minPercent: 88,
    maxPercent: 94,
    color: "hsl(270, 75%, 55%)",  // Purple (primary color)
    description: "Sweet spot training"
  },
  {
    zone: "Z5",
    name: "Threshold",
    minPercent: 95,
    maxPercent: 105,
    color: "hsl(25, 95%, 53%)",   // Orange
    description: "Lactate threshold"
  },
  {
    zone: "Z6",
    name: "VO2 Max",
    minPercent: 106,
    maxPercent: 120,
    color: "hsl(0, 84%, 60%)",    // Red
    description: "VO2 max intervals"
  },
  {
    zone: "Z7",
    name: "Anaerobic",
    minPercent: 121,
    maxPercent: 999,
    color: "hsl(340, 82%, 52%)",  // Dark red/magenta
    description: "Anaerobic capacity"
  }
];

// Calculate which training zone a power value falls into
export function calculateTrainingZone(power: number, ftp: number): TrainingZone {
  const percent = getPowerPercent(power, ftp);

  for (const zone of TRAINING_ZONES) {
    if (percent >= zone.minPercent && percent <= zone.maxPercent) {
      return zone.zone;
    }
  }

  return "Z1"; // Default to Z1 if somehow out of range
}

// Get training zone definition
export function getTrainingZoneDefinition(zone: TrainingZone): ZoneDefinition {
  return TRAINING_ZONES.find(z => z.zone === zone) || TRAINING_ZONES[0];
}

// Get color for training zone
export function getTrainingZoneColor(zone: TrainingZone): string {
  return getTrainingZoneDefinition(zone).color;
}
