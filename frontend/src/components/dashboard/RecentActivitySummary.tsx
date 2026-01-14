"use client";

import React from "react";
import type { RecentActivity } from "@/types/dashboard";
import { Bike, Activity, Waves } from "lucide-react";

interface RecentActivitySummaryProps {
  data: RecentActivity[];
}

export function RecentActivitySummary({ data }: RecentActivitySummaryProps) {

  const getActivityIcon = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("ride") || n.includes("cycle")) return <Bike className="w-4 h-4" />;
    if (n.includes("swim")) return <Waves className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  const getIconStyles = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes("ride") || n.includes("interval"))
      return "bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400";
    if (n.includes("swim"))
      return "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400";
    return "bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400";
  }

  return (
    <section className="bg-card-light dark:bg-card-dark rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-5 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
        <h2 className="font-semibold text-lg">Recent Activities</h2>
      </div>
      <div className="overflow-x-auto">
        {data.length === 0 ? (
          <div className="p-8 text-center text-subtext-light">No recent activities</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">Date</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">Activity</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">Duration</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">Distance</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">Avg Power</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">NP</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">IF</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-subtext-light dark:text-subtext-dark uppercase tracking-wider">TSS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {data.map((activity, index) => (
                <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
                  <td className="px-4 py-3 text-sm text-text-light dark:text-text-dark whitespace-nowrap">
                    {new Date(activity.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${getIconStyles(activity.name || "")}`}>
                        {getActivityIcon(activity.name || "")}
                      </div>
                      <span className="text-sm font-medium text-text-light dark:text-text-dark truncate max-w-xs">
                        {activity.name || "Untitled Activity"}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-center text-text-light dark:text-text-dark whitespace-nowrap">
                    {formatDuration(activity.duration)}
                  </td>
                  <td className="px-4 py-3 text-sm text-center text-text-light dark:text-text-dark whitespace-nowrap">
                    {activity.distance_km ? `${activity.distance_km.toFixed(1)} km` : "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-center text-text-light dark:text-text-dark whitespace-nowrap">
                    {activity.avg_power ? `${Math.round(activity.avg_power)}W` : "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-center text-text-light dark:text-text-dark whitespace-nowrap">
                    {activity.np ? `${Math.round(activity.np)}W` : "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-center text-text-light dark:text-text-dark whitespace-nowrap">
                    {activity.if ? activity.if.toFixed(2) : "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-center font-semibold text-text-light dark:text-text-dark whitespace-nowrap">
                    {Math.round(activity.tss || 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
