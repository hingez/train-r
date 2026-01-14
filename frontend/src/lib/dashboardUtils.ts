/**
 * Utility functions for dashboard data formatting and display.
 */

/**
 * Format duration in seconds to human-readable string (HH:MM:SS or MM:SS).
 *
 * @param seconds - Duration in seconds
 * @returns Formatted duration string
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }
  return `${minutes}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Format ISO date string to readable format (e.g., "Jan 15").
 *
 * @param isoDate - ISO date string (YYYY-MM-DD)
 * @returns Formatted date string
 */
export function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

/**
 * Format week start date to readable format (e.g., "Jan 15").
 *
 * @param isoDate - ISO date string (YYYY-MM-DD)
 * @returns Formatted week string
 */
export function formatWeek(isoDate: string): string {
  return formatDate(isoDate);
}

/**
 * Get color for training zone (1-5).
 *
 * @param zone - Zone number (1-5)
 * @returns Hex color code
 */
export function getZoneColor(zone: number): string {
  const zoneColors: Record<number, string> = {
    1: "#3b82f6", // blue - recovery
    2: "#10b981", // green - endurance
    3: "#fbbf24", // yellow - tempo
    4: "#f97316", // orange - threshold
    5: "#ef4444", // red - VO2 max
  };

  return zoneColors[zone] || "#6b7280"; // gray fallback
}

/**
 * Calculate week range string from week start date.
 *
 * @param weekStart - ISO date string for week start (Monday)
 * @returns Week range string (e.g., "Jan 15 - Jan 21")
 */
export function calculateWeekRange(weekStart: string): string {
  const startDate = new Date(weekStart);
  const endDate = new Date(startDate);
  endDate.setDate(endDate.getDate() + 6); // Add 6 days for Sunday

  const startMonth = startDate.toLocaleDateString("en-US", { month: "short" });
  const startDay = startDate.getDate();
  const endMonth = endDate.toLocaleDateString("en-US", { month: "short" });
  const endDay = endDate.getDate();

  // Same month
  if (startMonth === endMonth) {
    return `${startMonth} ${startDay} - ${endDay}`;
  }

  // Different months
  return `${startMonth} ${startDay} - ${endMonth} ${endDay}`;
}

/**
 * Format watts to readable string with unit.
 *
 * @param watts - Power in watts
 * @returns Formatted power string (e.g., "250W")
 */
export function formatWatts(watts: number): string {
  return `${Math.round(watts)}W`;
}

/**
 * Format TSS to readable string.
 *
 * @param tss - Training Stress Score
 * @returns Formatted TSS string
 */
export function formatTSS(tss: number): string {
  return Math.round(tss).toString();
}

/**
 * Format Intensity Factor to 2 decimal places.
 *
 * @param intensityFactor - IF value
 * @returns Formatted IF string
 */
export function formatIF(intensityFactor: number): string {
  return intensityFactor.toFixed(2);
}

/**
 * Format distance in km to readable string.
 *
 * @param km - Distance in kilometers
 * @returns Formatted distance string (e.g., "45.2 km")
 */
export function formatDistance(km: number): string {
  return `${km.toFixed(1)} km`;
}

/**
 * Format time in hours to readable string.
 *
 * @param hours - Time in hours
 * @returns Formatted time string (e.g., "12.5h")
 */
export function formatHours(hours: number): string {
  return `${hours.toFixed(1)}h`;
}
