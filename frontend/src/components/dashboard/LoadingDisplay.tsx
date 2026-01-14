"use client";

import React from "react";
import { CyclistClimbingAnimation } from "@/components/ui/cyclist-climbing-animation";

interface LoadingDisplayProps {
  message?: string;
}

export function LoadingDisplay({ message }: LoadingDisplayProps) {
  return (
    <div className="w-full h-full flex items-center justify-center p-6 bg-gradient-to-b from-background-light to-gray-50 dark:from-background-dark dark:to-gray-900">
      <div className="flex flex-col items-center gap-6 max-w-md">
        <CyclistClimbingAnimation />
        {message && (
          <p className="text-center text-gray-600 dark:text-gray-400 text-lg font-medium">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
