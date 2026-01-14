"use client";

import React from "react";
import { WeeklyLoadChart } from "./WeeklyLoadChart";
import { PowerCurveChart } from "./PowerCurveChart";
import { RecentActivitySummary } from "./RecentActivitySummary";
import type { DashboardData } from "@/types/dashboard";

interface DashboardProps {
  dashboardData: DashboardData;
}

export function Dashboard({ dashboardData }: DashboardProps) {
  const {
    weekly_load,
    power_curve,
    recent_activities,
  } = dashboardData;

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark font-sans antialiased pb-24 transition-colors duration-200">
      {/* Header - Fixed or Sticky if needed, mimicking the design's header inside the specific dashboard view if it's not global */}
      <header className="sticky top-0 z-30 bg-card-light/90 dark:bg-card-dark/90 backdrop-blur-md shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Train-R</h1>
            <p className="text-xs text-subtext-light dark:text-subtext-dark mt-0.5">Your Performance</p>
          </div>
        </div>
      </header>

      <main className="px-4 py-6 space-y-6 max-w-2xl mx-auto lg:max-w-7xl">
        {/* Charts Section */}
        <section>
          <WeeklyLoadChart data={weekly_load} />
        </section>

        <section>
          <PowerCurveChart data={power_curve} />
        </section>

        <section>
          <RecentActivitySummary data={recent_activities} />
        </section>
      </main>
    </div>
  );
}
