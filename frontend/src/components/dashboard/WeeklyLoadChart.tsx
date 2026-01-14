"use client";

import React, { useRef, useEffect } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ScriptableContext
} from "chart.js";
import { Bar } from "react-chartjs-2";
import type { WeeklyLoad } from "@/types/dashboard";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface WeeklyLoadChartProps {
  data: WeeklyLoad[];
}

export function WeeklyLoadChart({ data }: WeeklyLoadChartProps) {
  const chartRef = useRef<ChartJS<"bar">>(null);
  const [selectedMetric, setSelectedMetric] = React.useState<"TSS" | "Time" | "Dist" | "CTL">("TSS");
  const [timeRange, setTimeRange] = React.useState<"1M" | "3M" | "1Y">("3M");

  // Filter data based on time range
  const filteredData = React.useMemo(() => {
    let weeks = 13;
    if (timeRange === "1M") weeks = 4;
    if (timeRange === "1Y") weeks = 52;
    // Data is coming in chronological order (oldest -> newest), so we take the last N items
    return data.slice(-weeks);
  }, [data, timeRange]);

  const labels = filteredData.map((d) => {
    const date = new Date(d.week_start);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  });

  const datasetData = filteredData.map((d) => {
    if (selectedMetric === "Time") return d.total_time_hours;
    if (selectedMetric === "Dist") return d.total_distance_km;
    // @ts-ignore - ctl property added in backend but maybe not in type yet
    if (selectedMetric === "CTL") return d.ctl;
    return d.total_tss;
  });

  const chartData = {
    labels,
    datasets: [
      {
        label: selectedMetric,
        data: datasetData,
        backgroundColor: (context: ScriptableContext<"bar">) => {
          const ctx = context.chart.ctx;
          const gradient = ctx.createLinearGradient(0, 0, 0, 300);

          if (selectedMetric === "CTL") {
            // Different color for CTL (fitness) - maybe Blue or Pink?
            gradient.addColorStop(0, "rgba(59, 130, 246, 0.8)"); // Blue-500
            gradient.addColorStop(1, "rgba(59, 130, 246, 0.4)");
          } else {
            gradient.addColorStop(0, "rgba(139, 92, 246, 0.8)"); // Primary Purple
            gradient.addColorStop(1, "rgba(139, 92, 246, 0.4)");
          }
          return gradient;
        },
        borderRadius: 4,
        barPercentage: 0.9,
        categoryPercentage: 0.9,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(17, 24, 39, 0.9)",
        titleColor: "#fff",
        bodyColor: "#fff",
        padding: 10,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          // @ts-ignore
          label: (context) => {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              if (selectedMetric === 'Time') label += context.parsed.y + ' hrs';
              else if (selectedMetric === 'Dist') label += context.parsed.y + ' km';
              else if (selectedMetric === 'CTL') label += context.parsed.y;
              else label += context.parsed.y + ' TSS';
            }
            return label;
          }
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: "rgba(156, 163, 175, 0.1)",
          borderDash: [5, 5],
        },
        ticks: { font: { family: "var(--font-geist-sans)", size: 10 }, color: "#9CA3AF" },
        border: { display: false },
      },
      x: {
        grid: { display: false },
        ticks: {
          maxRotation: 45,
          minRotation: 45,
          font: { family: "var(--font-geist-sans)", size: 9 },
          color: "#9CA3AF",
          autoSkip: true,
          maxTicksLimit: timeRange === '1Y' ? 12 : 8,
        },
        border: { display: false },
      },
    },
  };

  const metricLabel = selectedMetric === "TSS" ? "TSS (Training Stress Score)" : selectedMetric === "Time" ? "Time (Hours)" : selectedMetric === "Dist" ? "Distance (km)" : "CTL (Chronic Training Load)";


  return (
    <div className="bg-card-light dark:bg-card-dark rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden h-full flex flex-col">
      <div className="p-5 border-b border-gray-100 dark:border-gray-700 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h2 className="font-semibold text-lg">Weekly Training Load</h2>
          <div className="flex items-center gap-2 mt-1">
            <button
              onClick={() => setTimeRange("1M")}
              className={`text-xs px-2 py-0.5 rounded-full transition-colors ${timeRange === "1M" ? "bg-gray-200 dark:bg-gray-700 font-medium" : "text-subtext-light dark:text-subtext-dark hover:bg-gray-100 dark:hover:bg-gray-800"}`}
            >
              1M
            </button>
            <button
              onClick={() => setTimeRange("3M")}
              className={`text-xs px-2 py-0.5 rounded-full transition-colors ${timeRange === "3M" ? "bg-gray-200 dark:bg-gray-700 font-medium" : "text-subtext-light dark:text-subtext-dark hover:bg-gray-100 dark:hover:bg-gray-800"}`}
            >
              3M
            </button>
            <button
              onClick={() => setTimeRange("1Y")}
              className={`text-xs px-2 py-0.5 rounded-full transition-colors ${timeRange === "1Y" ? "bg-gray-200 dark:bg-gray-700 font-medium" : "text-subtext-light dark:text-subtext-dark hover:bg-gray-100 dark:hover:bg-gray-800"}`}
            >
              1Y
            </button>
          </div>
        </div>
        <div className="bg-gray-100 dark:bg-gray-800 p-1 rounded-lg flex self-start sm:self-auto">
          {["TSS", "Time", "Dist", "CTL"].map((m) => (
            <button
              key={m}
              onClick={() => setSelectedMetric(m as any)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${selectedMetric === m
                ? "bg-primary text-white shadow-sm"
                : "text-subtext-light dark:text-subtext-dark hover:text-text-light dark:hover:text-text-dark hover:bg-gray-200 dark:hover:bg-gray-700"
                }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>
      <div className="p-5 flex-1 h-[400px]">
        <div className="relative h-full w-full">
          {/* @ts-ignore - ref types mismatch sometimes with react-chartjs-2 */}
          <Bar ref={chartRef} data={chartData} options={options} />
        </div>
      </div>
      <div className="p-4 pt-0 flex items-center justify-center gap-2">
        <span className="w-3 h-3 bg-primary rounded-sm"></span>
        <span className="text-xs font-medium text-subtext-light dark:text-subtext-dark">{metricLabel}</span>
      </div>
    </div>
  );
}
