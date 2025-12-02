import { useState, useEffect } from "react";
import { Spinner } from "./spinner";

const CYCLING_PHRASES = [
  "Calculating the derivative of your cadence...",
  "Integrating your power curve...",
  "Solving for optimal torque vectors...",
  "Measuring pedal stroke entropy...",
  "Calibrating your velocity coefficient...",
  "Computing lactate threshold matrices...",
  "Factoring your heart rate polynomial...",
  "Normalizing watts per kilogram...",
  "Triangulating your training load...",
  "Graphing interval amplitude...",
  "Balancing your effort equation...",
  "Extrapolating recovery trajectories...",
  "Mapping your fitness gradient...",
  "Quantifying aerobic momentum...",
  "Plotting threshold asymptotes...",
  "Resolving power output frequencies...",
  "Indexing your endurance spectrum...",
  "Measuring cadence wavelengths...",
  "Computing your FTP tangent...",
  "Analyzing pedal force distribution...",
  "Calculating training stress variance...",
  "Optimizing your performance radius...",
  "Synthesizing your power profile...",
  "Evaluating your VO2 function...",
  "Determining your effort magnitude...",
  "Deriving your wattage function...",
  "Computing zone transition coefficients...",
  "Calibrating your rpm oscillations...",
  "Mapping cadence harmonics...",
  "Solving for peak power coordinates...",
  "Measuring your fitness derivative...",
  "Integrating interval intensity curves...",
  "Calculating your effort eigenvalues...",
  "Normalizing heart rate distributions...",
  "Triangulating your training zones...",
  "Graphing recovery exponentials...",
  "Factoring your endurance matrix...",
  "Extrapolating power band trajectories...",
  "Plotting your aerobic ceiling...",
  "Quantifying torque acceleration...",
  "Resolving threshold frequencies...",
  "Indexing your performance spectrum...",
  "Balancing metabolic equations...",
  "Computing your cadence quotient...",
  "Analyzing pedal efficiency vectors...",
  "Measuring training load variance...",
  "Optimizing your power curve radius...",
  "Synthesizing VO2 max parameters...",
  "Evaluating your effort polynomial...",
  "Determining interval magnitude...",
  "Calculating your training stress integral...",
  "Mapping power zone topology...",
  "Solving for cadence equilibrium...",
  "Measuring your fitness trajectory...",
  "Calibrating heart rate amplitude...",
  "Computing your threshold gradient...",
  "Integrating pedal stroke mechanics...",
  "Normalizing your effort distribution...",
  "Triangulating recovery vectors...",
  "Graphing your endurance function...",
  "Factoring interval load matrices...",
  "Extrapolating power output trends...",
  "Plotting your anaerobic threshold...",
  "Quantifying training momentum...",
  "Resolving your rpm harmonics...",
  "Indexing performance coefficients...",
  "Balancing your power equation...",
  "Computing FTP derivatives...",
  "Analyzing your effort spectrum...",
  "Measuring cadence periodicity...",
  "Optimizing torque efficiency...",
  "Synthesizing your fitness profile...",
  "Evaluating zone transition points...",
  "Determining your wattage tangent...",
  "Calculating pedal force ratios...",
  "Deriving your interval intensity matrix...",
  "Computing your power band frequencies...",
  "Calibrating threshold oscillations...",
  "Mapping your endurance coordinates...",
  "Solving for optimal cadence vectors...",
  "Measuring training load entropy...",
  "Integrating your heart rate curve...",
  "Calculating aerobic capacity functions...",
  "Normalizing your effort wavelengths...",
  "Triangulating power output zones...",
  "Graphing your recovery parabola...",
  "Factoring pedal stroke coefficients...",
  "Extrapolating your fitness arc...",
  "Plotting VO2 asymptotes...",
  "Quantifying your training radius...",
  "Resolving cadence distributions...",
  "Indexing your threshold spectrum...",
  "Balancing metabolic load equations...",
  "Computing your torque polynomial...",
  "Analyzing interval amplitude peaks...",
  "Measuring your power gradient...",
  "Optimizing performance trajectories...",
  "Synthesizing effort magnitude...",
  "Evaluating your rpm eigenvalues...",
  "Determining pedal efficiency quotients...",

];

export function CyclingLoadingSpinner() {
  const [currentPhrase, setCurrentPhrase] = useState(() => {
    // Select a random phrase on initial render
    return CYCLING_PHRASES[Math.floor(Math.random() * CYCLING_PHRASES.length)];
  });

  useEffect(() => {
    // Change phrase every 5 seconds
    const interval = setInterval(() => {
      setCurrentPhrase(
        CYCLING_PHRASES[Math.floor(Math.random() * CYCLING_PHRASES.length)]
      );
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-3">
      <Spinner variant="circle" size={16} className="text-muted-foreground" />
      <span className="text-sm text-muted-foreground">{currentPhrase}</span>
    </div>
  );
}
