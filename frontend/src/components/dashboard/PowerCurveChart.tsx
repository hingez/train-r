"use client";

import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { PowerCurveData, PowerCurvePoint } from "@/types/dashboard";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PowerCurveChartProps {
  data: PowerCurveData;
}

export function PowerCurveChart({ data }: PowerCurveChartProps) {
  // Sort both datasets by duration
  const thirtyDaySorted = [...data.thirty_day].sort((a, b) => a.duration_seconds - b.duration_seconds);
  const allTimeSorted = [...data.all_time].sort((a, b) => a.duration_seconds - b.duration_seconds);

  // Get all unique durations from both datasets
  const allDurations = new Set([
    ...thirtyDaySorted.map(d => d.duration_seconds),
    ...allTimeSorted.map(d => d.duration_seconds)
  ]);
  const sortedDurations = Array.from(allDurations).sort((a, b) => a - b);

  // Use all durations for the chart
  const labels = sortedDurations.map(seconds => {
    const point = thirtyDaySorted.find(d => d.duration_seconds === seconds) ||
                  allTimeSorted.find(d => d.duration_seconds === seconds);
    return point?.duration || "";
  });

  const thirtyDayPowerValues = sortedDurations.map(seconds => {
    return thirtyDaySorted.find(d => d.duration_seconds === seconds)?.watts || null;
  });

  const allTimePowerValues = sortedDurations.map(seconds => {
    return allTimeSorted.find(d => d.duration_seconds === seconds)?.watts || null;
  });

  const chartData = {
    labels,
    datasets: [
      {
        label: "30 Day",
        data: thirtyDayPowerValues,
        borderColor: "#8B5CF6",
        backgroundColor: "rgba(139, 92, 246, 0.1)",
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: "#8B5CF6",
        pointBorderColor: "#8B5CF6",
        pointHoverBackgroundColor: "#8B5CF6",
        pointHoverBorderColor: "#fff",
        pointHoverBorderWidth: 2,
        borderDash: [], // Solid line
      },
      {
        label: "All Time",
        data: allTimePowerValues,
        borderColor: "#10B981",
        backgroundColor: "transparent",
        borderWidth: 2,
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: "#10B981",
        pointBorderColor: "#10B981",
        pointHoverBackgroundColor: "#10B981",
        pointHoverBorderColor: "#fff",
        pointHoverBorderWidth: 2,
        borderDash: [5, 5], // Dotted line
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        align: 'end' as const,
        labels: {
          color: '#9CA3AF',
          usePointStyle: true,
          pointStyle: 'line',
          padding: 15,
          font: {
            size: 11,
            weight: '500' as const,
          }
        }
      },
      tooltip: {
        enabled: true,
        mode: 'index' as const,
        intersect: false,
        backgroundColor: "rgba(17, 24, 39, 0.9)",
        titleColor: "#fff",
        bodyColor: "#fff",
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        borderColor: "rgba(255, 255, 255, 0.1)",
        borderWidth: 1,
        callbacks: {
          title: (items: any) => `${items[0].label}`,
          label: (item: any) => {
            if (item.raw === null) return null;
            return `${item.dataset.label}: ${item.raw}W`;
          }
        }
      },
    },
    scales: {
      y: { display: false },
      x: {
        display: true,
        grid: {
          display: false,
        },
        border: {
          display: false,
        },
        ticks: {
          color: '#9CA3AF',
          font: {
            size: 10,
            weight: '500' as const,
          },
          padding: 8,
        }
      },
    },
    layout: { padding: 0 },
  };

  // Extract key stats from both 30-day and all-time data
  const stats = [
    { duration: "5s", seconds: 5 },
    { duration: "30s", seconds: 30 },
    { duration: "1min", seconds: 60 },
    { duration: "5min", seconds: 300 },
    { duration: "15min", seconds: 900 },
    { duration: "20min", seconds: 1200 },
    { duration: "30min", seconds: 1800 },
  ];

  const statsData = stats.map(stat => ({
    duration: stat.duration,
    thirtyDay: data.thirty_day.find(d => d.duration_seconds === stat.seconds)?.watts || 0,
    allTime: data.all_time.find(d => d.duration_seconds === stat.seconds)?.watts || 0,
  }));

  return (
    <section className="bg-card-light dark:bg-card-dark rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden h-full flex flex-col">
      <div className="p-5 border-b border-gray-100 dark:border-gray-700">
        <h2 className="font-semibold text-lg">Power Curve</h2>
      </div>
      <div className="p-5 flex-1 flex flex-col">
        <div className="flex-1 relative min-h-[200px] w-full bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center">
          <div className="w-full h-full p-2 absolute inset-0">
            {/* @ts-ignore */}
            <Line data={chartData} options={options} />
          </div>
        </div>
        <div className="mt-4 flex items-start gap-3">
          <div className="flex flex-col gap-1.5 text-xs font-medium pt-1">
            <div className="flex items-center gap-1.5">
              <span style={{ color: "#8B5CF6" }}>30 Day</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span style={{ color: "#10B981" }}>All Time</span>
            </div>
          </div>
          <div className="grid grid-cols-7 gap-2 text-center flex-1">
            {statsData.map((stat, index) => (
              <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2">
                <p className="text-[10px] text-subtext-light dark:text-subtext-dark uppercase font-bold tracking-wider mb-1.5">
                  {stat.duration}
                </p>
                <div className="space-y-0.5">
                  <p className="text-sm font-bold" style={{ color: "#8B5CF6" }}>
                    {stat.thirtyDay}W
                  </p>
                  <p className="text-xs font-semibold" style={{ color: "#10B981" }}>
                    {stat.allTime}W
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
