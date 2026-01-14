import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";
import type { TrainingPlan } from "@/types/trainingPlan";
import { isRecoveryWeek } from "@/lib/trainingPlanUtils";

interface ProgressionChartProps {
  plan: TrainingPlan;
}

export function ProgressionChart({ plan }: ProgressionChartProps) {
  // Prepare chart data
  const chartData: Array<{
    week: number;
    tss: number;
    hours: number;
    isRecovery: boolean;
    phase: string;
  }> = [];
  let weekNumber = 0;

  plan.training_plan.forEach((phase) => {
    phase.weeks.forEach((week) => {
      weekNumber++;
      const isRecovery = isRecoveryWeek(week.target_hours, phase.weeks);

      chartData.push({
        week: weekNumber,
        tss: week.target_tss,
        hours: week.target_hours,
        isRecovery,
        phase: phase.phase_name
      });
    });
  });

  return (
    <section className="bg-card-light dark:bg-card-dark rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
      <div className="p-5 border-b border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-lg">Weekly Load Progression</h3>
      </div>
      <div className="p-5">
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData}>
            <CartesianGrid
              strokeDasharray="5 5"
              stroke="rgba(156, 163, 175, 0.1)"
              vertical={false}
            />
            <XAxis
              dataKey="week"
              label={{ value: "Week", position: "insideBottom", offset: -5, style: { fontSize: 10, fill: '#9CA3AF' } }}
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="left"
              label={{ value: "TSS", angle: -90, position: "insideLeft", style: { fontSize: 10, fill: '#9CA3AF' } }}
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: "Hours", angle: 90, position: "insideRight", style: { fontSize: 10, fill: '#9CA3AF' } }}
              tick={{ fontSize: 10, fill: '#9CA3AF' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(17, 24, 39, 0.9)",
                border: "none",
                borderRadius: "8px",
                color: "#fff",
                padding: "10px"
              }}
              labelStyle={{ color: "#fff", fontWeight: 600 }}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', fontWeight: 500, paddingTop: '10px' }}
            />

            {/* Recovery weeks as reference lines */}
            {chartData.map((data, idx) =>
              data.isRecovery ? (
                <ReferenceLine
                  key={idx}
                  x={data.week}
                  stroke="#9CA3AF"
                  strokeDasharray="3 3"
                  opacity={0.3}
                />
              ) : null
            )}

            <Bar
              yAxisId="left"
              dataKey="tss"
              fill="#8B5CF6"
              name="TSS"
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="hours"
              stroke="#10B981"
              strokeWidth={2}
              name="Hours"
              dot={{ r: 3, fill: "#10B981" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
