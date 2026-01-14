"use client";

import React from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import type { ZoneDistribution } from "@/types/dashboard";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface ZoneDistributionChartProps {
  data: ZoneDistribution[];
}

export function ZoneDistributionChart({ data }: ZoneDistributionChartProps) {
  // Aggregate data for simpler mobile friendly view (or use first week if that's the intent)
  // The screenshot implies a summary distribution, let's sum up all weeks for a "Distribution" view
  // OR just use labels Z1-Z6 and data from the latest week or average.
  // Given "Training Zone Distribution" usually means overall, let's average or sum.
  // Actually, let's keep it simple and just show the latest week or aggregated data as per the chart type in snippet (Bar Z1-Z6)

  // Aggregate hours per zone
  const totals = {
    Z1: 0, Z2: 0, Z3: 0, Z4: 0, Z5: 0, Z6: 0
  };

  data.forEach(d => {
    totals.Z1 += d.zone_1_hours;
    totals.Z2 += d.zone_2_hours;
    totals.Z3 += d.zone_3_hours;
    totals.Z4 += d.zone_4_hours;
    totals.Z5 += d.zone_5_hours;
    // Z6 missing in type? assuming Z6 is anaerobic/neuromuscular, often lumped into Z5 or Z6.
    // If type doesn't have Z6, we'll skip or add mock if needed.
  });

  const labels = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5'];

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Hours',
        data: [totals.Z1, totals.Z2, totals.Z3, totals.Z4, totals.Z5],
        // Use different colors for zones
        backgroundColor: [
          '#10B981', // Z1 - Green
          '#10B981', // Z2 - Green
          '#F59E0B', // Z3 - Yellow
          '#F59E0B', // Z4 - Orange/Amb
          '#EF4444', // Z5 - Red
        ],
        borderRadius: 4,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(156, 163, 175, 0.1)',
          borderDash: [5, 5]
        },
        ticks: { font: { size: 10 }, color: '#9CA3AF' }
      },
      x: {
        grid: { display: false },
        ticks: { font: { size: 10 }, color: '#9CA3AF' }
      }
    }
  };


  return (
    <section className="bg-card-light dark:bg-card-dark rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden h-full flex flex-col">
      <div className="p-5 border-b border-gray-100 dark:border-gray-700">
        <h2 className="font-semibold text-lg">Training Zone Distribution</h2>
      </div>
      <div className="p-5 flex-1 min-h-[200px]">
        <div className="relative h-full w-full">
          {/* @ts-ignore */}
          <Bar data={chartData} options={options} />
        </div>
      </div>
    </section>
  );
}
