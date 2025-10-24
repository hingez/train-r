"""Script to generate structured .fit workout files programmatically.

This script creates randomized cycling workouts across 5 different types:
- VO2max Intervals
- Threshold/FTP Intervals
- Sweet Spot
- Endurance/Z2
- Pyramid/Progression

Requirements:
    pip install fit-tool

Usage:
    python -m src.scripts.generate_fit_workout
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

try:
    from fit_tool.fit_file_builder import FitFileBuilder
    from fit_tool.profile.messages.workout_step_message import WorkoutStepMessage
    from fit_tool.profile.messages.workout_message import WorkoutMessage
    from fit_tool.profile.profile_type import Sport, Intensity, WorkoutStepDuration, WorkoutStepTarget
except ImportError:
    print("Error: fit-tool library not installed")
    print("Install with: uv add fit-tool")
    sys.exit(1)

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class WorkoutGenerator:
    """Generate structured cycling workouts as .fit files."""

    def __init__(self, ftp: int, total_duration: int):
        """Initialize workout generator.

        Args:
            ftp: Functional Threshold Power in watts
            total_duration: Total workout duration in minutes
        """
        self.ftp = ftp
        self.total_duration = total_duration
        self.workout_steps = []

    def _add_step(self, duration_minutes: float, intensity_pct: float,
                  step_name: str = "", cadence: int = None) -> None:
        """Add a workout step.

        Args:
            duration_minutes: Duration in minutes
            intensity_pct: Intensity as percentage of FTP (0-200)
            step_name: Name/description of the step
            cadence: Optional target cadence in RPM
        """
        duration_seconds = int(duration_minutes * 60)
        target_power = int(self.ftp * (intensity_pct / 100))

        self.workout_steps.append({
            'duration': duration_seconds,
            'power': target_power,
            'name': step_name,
            'cadence': cadence
        })

    def _calculate_remaining_time(self) -> int:
        """Calculate remaining time after warmup/cooldown.

        Returns:
            Remaining minutes for main workout
        """
        used_time = sum(step['duration'] for step in self.workout_steps) / 60
        return int(self.total_duration - used_time)

    def generate_vo2max(self) -> List[Dict]:
        """Generate VO2max interval workout.

        Structure: Warmup → High-intensity repeats → Cooldown
        Intensity: 110-120% FTP
        Intervals: 3-5 minutes, 4-8 repeats
        Recovery: 50-60% FTP, equal or longer than work interval
        """
        self.workout_steps = []

        # Randomize parameters
        warmup = random.randint(10, 15)
        cooldown = random.randint(5, 10)
        interval_duration = random.choice([3, 3.5, 4, 4.5, 5])
        num_intervals = random.randint(4, 8)
        intensity = random.randint(110, 120)
        recovery_multiplier = random.choice([1.0, 1.25, 1.5])
        recovery_duration = interval_duration * recovery_multiplier
        recovery_intensity = random.randint(50, 60)

        # Build workout
        self._add_step(warmup, 65, "Warmup")

        for i in range(num_intervals):
            self._add_step(interval_duration, intensity, f"VO2max Interval {i+1}")
            if i < num_intervals - 1:  # No recovery after last interval
                self._add_step(recovery_duration, recovery_intensity, f"Recovery {i+1}")

        self._add_step(cooldown, 55, "Cooldown")

        return self.workout_steps

    def generate_threshold(self) -> List[Dict]:
        """Generate Threshold/FTP interval workout.

        Structure: Warmup → Sustained efforts → Cooldown
        Intensity: 95-105% FTP
        Intervals: 8-20 minutes, 2-5 repeats
        Recovery: 3-7 minutes at 50-60% FTP
        """
        self.workout_steps = []

        # Randomize parameters
        warmup = random.randint(15, 20)
        cooldown = random.randint(10, 15)
        interval_duration = random.choice([8, 10, 12, 15, 20])
        num_intervals = random.randint(2, 5)
        intensity = random.choice([95, 100, 105])
        recovery_duration = random.randint(3, 7)
        recovery_intensity = random.randint(50, 60)

        # Build workout
        self._add_step(warmup, 65, "Warmup")

        for i in range(num_intervals):
            self._add_step(interval_duration, intensity, f"Threshold Interval {i+1}")
            if i < num_intervals - 1:
                self._add_step(recovery_duration, recovery_intensity, f"Recovery {i+1}")

        self._add_step(cooldown, 55, "Cooldown")

        return self.workout_steps

    def generate_sweet_spot(self) -> List[Dict]:
        """Generate Sweet Spot workout.

        Structure: Warmup → Long sustained efforts → Cooldown
        Intensity: 86-95% FTP
        Intervals: 10-25 minutes, 2-4 repeats
        Recovery: 5-10 minutes at 55-65% FTP
        """
        self.workout_steps = []

        # Randomize parameters
        warmup = random.randint(10, 15)
        cooldown = random.randint(5, 10)
        interval_duration = random.choice([10, 15, 20, 25])
        num_intervals = random.randint(2, 4)
        intensity = random.choice([86, 88, 90, 92, 95])
        recovery_duration = random.randint(5, 10)
        recovery_intensity = random.randint(55, 65)

        # Build workout
        self._add_step(warmup, 65, "Warmup")

        for i in range(num_intervals):
            self._add_step(interval_duration, intensity, f"Sweet Spot Interval {i+1}")
            if i < num_intervals - 1:
                self._add_step(recovery_duration, recovery_intensity, f"Recovery {i+1}")

        self._add_step(cooldown, 55, "Cooldown")

        return self.workout_steps

    def generate_endurance(self) -> List[Dict]:
        """Generate Endurance/Z2 workout.

        Structure: Warmup → Long steady → Cooldown
        Intensity: 55-75% FTP
        Duration: Main block uses most of available time
        Optional: Micro-intervals and cadence drills
        """
        self.workout_steps = []

        # Randomize parameters
        warmup = random.randint(5, 10)
        cooldown = 5
        include_micro = random.choice([True, False])
        include_cadence = random.choice([True, False])
        base_intensity = random.randint(56, 75)

        # Build workout
        self._add_step(warmup, 55, "Warmup")

        # Calculate main duration
        remaining = self.total_duration - warmup - cooldown

        if include_micro:
            # Add micro-intervals (3x 1min @ 85%)
            main_duration = remaining - 6  # 3 intervals + 3 recoveries
            segment_duration = main_duration / 4

            self._add_step(segment_duration, base_intensity, "Endurance")
            for i in range(3):
                self._add_step(1, 85, f"Micro Interval {i+1}")
                self._add_step(1, base_intensity, "Recovery")
            self._add_step(segment_duration, base_intensity, "Endurance")

        elif include_cadence:
            # Add cadence drills (5x 1min high cadence)
            num_drills = random.randint(3, 5)
            main_duration = remaining - num_drills * 2
            segment_duration = main_duration / (num_drills + 1)

            for i in range(num_drills):
                self._add_step(segment_duration, base_intensity, "Endurance")
                self._add_step(1, base_intensity, f"High Cadence {i+1}", cadence=105)
                self._add_step(1, base_intensity, "Normal Cadence")
            self._add_step(segment_duration, base_intensity, "Endurance")

        else:
            # Simple steady state
            self._add_step(remaining, base_intensity, "Endurance")

        self._add_step(cooldown, 50, "Cooldown")

        return self.workout_steps

    def generate_pyramid(self) -> List[Dict]:
        """Generate Pyramid/Progression workout.

        Structure: Warmup → Ascending/Descending intervals → Cooldown
        Intensity: Progresses from 70-80% to 100-110% FTP
        Pattern: Various ascending/descending/pyramid patterns
        """
        self.workout_steps = []

        # Randomize parameters
        warmup = random.randint(10, 15)
        cooldown = 10
        pattern_type = random.choice(['ascending', 'descending', 'pyramid'])
        step_duration = random.choice([1, 2, 3, 4, 5])
        recovery_duration = random.randint(1, 3)

        # Build workout
        self._add_step(warmup, 65, "Warmup")

        if pattern_type == 'ascending':
            # Example: 1-2-3-4-5 minutes
            pattern = list(range(step_duration, step_duration * 6, step_duration))
        elif pattern_type == 'descending':
            # Example: 5-4-3-2-1 minutes
            pattern = list(range(step_duration * 5, 0, -step_duration))
        else:  # pyramid
            # Example: 1-2-3-4-3-2-1 or 2-4-6-8-6-4-2
            half = list(range(step_duration, step_duration * 5, step_duration))
            pattern = half + half[-2::-1]

        # Calculate intensities
        num_steps = len(pattern)
        start_intensity = random.randint(70, 80)
        peak_intensity = random.randint(100, 110)

        for i, duration in enumerate(pattern):
            # Calculate intensity for this step
            if pattern_type == 'ascending' or pattern_type == 'pyramid' and i < num_steps // 2:
                intensity = start_intensity + (peak_intensity - start_intensity) * (i / (num_steps - 1))
            else:
                intensity = peak_intensity - (peak_intensity - start_intensity) * ((i - num_steps // 2) / (num_steps // 2))

            self._add_step(duration, int(intensity), f"Interval {i+1}")
            if i < len(pattern) - 1:
                self._add_step(recovery_duration, 50, f"Recovery {i+1}")

        self._add_step(cooldown, 55, "Cooldown")

        return self.workout_steps

    def build_fit_file(self, workout_name: str, output_path: Path) -> None:
        """Build and save .fit file from workout steps.

        Args:
            workout_name: Name of the workout
            output_path: Path to save .fit file
        """
        builder = FitFileBuilder()

        # Create workout message
        workout_msg = WorkoutMessage()
        workout_msg.workout_name = workout_name
        workout_msg.sport = Sport.CYCLING
        workout_msg.num_valid_steps = len(self.workout_steps)

        # Add each step
        for idx, step in enumerate(self.workout_steps):
            step_msg = WorkoutStepMessage()
            step_msg.workout_step_name = step['name'] or f"Step {idx+1}"
            step_msg.intensity = Intensity.ACTIVE
            step_msg.duration_type = WorkoutStepDuration.TIME
            step_msg.duration_time = step['duration']
            step_msg.target_type = WorkoutStepTarget.POWER
            step_msg.target_value = step['power']

            if step.get('cadence'):
                step_msg.custom_target_value_low = step['cadence'] - 5
                step_msg.custom_target_value_high = step['cadence'] + 5

            builder.add_message(step_msg)

        builder.add_message(workout_msg)

        # Write file
        fit_file = builder.build()
        with open(output_path, 'wb') as f:
            fit_file.to_file(f)


def get_user_inputs() -> Tuple[int, int, str]:
    """Get user inputs for workout generation.

    Returns:
        Tuple of (ftp, duration, workout_type)
    """
    print("=== FIT Workout Generator ===\n")

    # Get FTP
    while True:
        try:
            ftp = int(input("Enter your FTP (watts): ").strip())
            if ftp > 0:
                break
            print("FTP must be positive")
        except ValueError:
            print("Please enter a valid number")

    # Get duration
    while True:
        try:
            duration = int(input("Enter total workout duration (minutes): ").strip())
            if duration > 0:
                break
            print("Duration must be positive")
        except ValueError:
            print("Please enter a valid number")

    # Get workout type
    print("\nWorkout Types:")
    print("1. VO2max Intervals (High-intensity 110-120% FTP)")
    print("2. Threshold/FTP Intervals (95-105% FTP)")
    print("3. Sweet Spot (86-95% FTP)")
    print("4. Endurance/Z2 (55-75% FTP)")
    print("5. Pyramid/Progression (70-110% FTP)")

    workout_types = {
        '1': 'vo2max',
        '2': 'threshold',
        '3': 'sweetspot',
        '4': 'endurance',
        '5': 'pyramid'
    }

    while True:
        choice = input("\nSelect workout type (1-5): ").strip()
        if choice in workout_types:
            return ftp, duration, workout_types[choice]
        print("Please enter a number between 1 and 5")


def main():
    """Main script execution."""
    # Get user inputs
    ftp, duration, workout_type = get_user_inputs()

    # Create generator
    generator = WorkoutGenerator(ftp, duration)

    # Generate workout
    print(f"\nGenerating {workout_type} workout...")

    if workout_type == 'vo2max':
        steps = generator.generate_vo2max()
        workout_name = "VO2max Intervals"
    elif workout_type == 'threshold':
        steps = generator.generate_threshold()
        workout_name = "Threshold Intervals"
    elif workout_type == 'sweetspot':
        steps = generator.generate_sweet_spot()
        workout_name = "Sweet Spot"
    elif workout_type == 'endurance':
        steps = generator.generate_endurance()
        workout_name = "Endurance"
    else:  # pyramid
        steps = generator.generate_pyramid()
        workout_name = "Pyramid Progression"

    # Display workout summary
    print(f"\n{workout_name} Workout Summary:")
    print("-" * 60)
    total_time = 0
    for step in steps:
        minutes = step['duration'] / 60
        total_time += minutes
        power_pct = (step['power'] / ftp) * 100
        cadence_info = f" @ {step['cadence']} rpm" if step.get('cadence') else ""
        print(f"  {step['name']:30s} {minutes:5.1f}min at {step['power']:3d}W ({power_pct:.0f}% FTP){cadence_info}")
    print("-" * 60)
    print(f"Total time: {total_time:.1f} minutes\n")

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{workout_type}_{timestamp}.fit"

    # Create output directory
    output_dir = PROJECT_ROOT / "data" / "generated_workouts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Build and save .fit file
    print(f"Saving workout to: {output_path}")
    generator.build_fit_file(workout_name, output_path)

    print(f"\nWorkout saved successfully!")
    print(f"File: {output_path}")


if __name__ == "__main__":
    main()
