import { useState, useEffect } from "react";
import { Spinner } from "./spinner";

const CYCLING_PHRASES = [
  "Spinning the gears...",
  "Chasing the breakaway...",
  "Hanging on the wheel...",
  "In the drops...",
  "Riding the rivet...",
  "Crushing the watts...",
  "Don't get dropped...",
  "Ticking over...",
  "Riding into the red...",
  "The sufferfest continues...",
  "Hitting the wall...",
  "Gapping the field...",
  "Finding the perfect cadence...",
  "Grinding up the climb...",
  "Drafting for success...",
  "Crossing the finish line...",
  "Getting a clean pull...",
  "Sprinting for the line...",
  "Going full gas...",
  "Hitting the power meter...",
  "Taking a bottle...",
  "Pedaling squares...",
  "Finding the sweet spot...",
  "Rolling on the flats...",
  "Looking for a headwind...",
  "Tightening the quick-release...",
  "Applying chamois cream...",
  "Pumping the tires...",
  "Checking the spoke tension...",
  "Adjusting the derailleurs...",
  "Lacing the spokes...",
  "Truing the wheel...",
  "Lubing the chain...",
  "Torquing the bolts...",
  "Indexing the shifting...",
  "Bleeding the brakes...",
  "Checking the bottom bracket...",
  "Installing the new cassette...",
  "Searching for the spare tube...",
  "Patching the flat...",
  "Setting the saddle height...",
  "Checking the tire pressure...",
  "Shedding the chain...",
  "Wrenching in the garage...",
  "Climbing Alpe d'Huez...",
  "Rolling over the Cobbles...",
  "Pounding the Pave...",
  "Riding the Koppenberg...",
  "Searching for Roubaix...",
  "Scaling the Stelvio...",
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
    <div className="flex items-center gap-3 text-muted-foreground">
      <Spinner variant="circle" size={16} />
      <span className="text-sm">{currentPhrase}</span>
    </div>
  );
}
